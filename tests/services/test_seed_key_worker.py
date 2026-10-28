import json
from pathlib import Path
import struct
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch

from services.seed_key_provider import (SeedKeyRequest, MockSeedKeyProvider, ProviderError,
                                       ProviderErrorCode, encode_request)
from services.can.seed_key_worker import ProcessWorkerTransport, ProcessMockSeedKeyProvider


WORKER = Path('build/security_worker/SeedKeyWorker.x86.exe').resolve()


class WorkerTransportTests(unittest.TestCase):
    def transport(self, code):
        transport = ProcessWorkerTransport([sys.executable, '-I', '-c', code])
        self.addCleanup(transport.close)
        return transport

    def test_timeout_and_cancel_reap_worker(self):
        for cancelled in (False, True):
            transport = self.transport('import time;time.sleep(10)')
            event = threading.Event()
            if cancelled: threading.Timer(.05, event.set).start()
            started = time.monotonic()
            with self.assertRaises(ProviderError) as error:
                transport.exchange(b'{}', timeout_s=.15, cancel=event)
            self.assertEqual(error.exception.code, ProviderErrorCode.CANCELLED if cancelled else ProviderErrorCode.TIMEOUT)
            self.assertLess(time.monotonic()-started, 2)
            self.assertIsNone(transport.active_pid)

    def test_crash_oversized_and_truncated_response_are_bounded(self):
        cases = [('import sys;sys.exit(7)', ProviderErrorCode.WORKER_CRASH),
                 ("import sys,struct;sys.stdout.buffer.write(struct.pack('<I',999999));sys.stdout.buffer.flush()", ProviderErrorCode.BAD_RESPONSE),
                 ("import sys,struct;sys.stdout.buffer.write(struct.pack('<I',4)+b'x');sys.stdout.buffer.flush()", ProviderErrorCode.BAD_RESPONSE)]
        for code, expected in cases:
            transport = self.transport(code)
            with self.assertRaises(ProviderError) as error:
                transport.exchange(b'{}', timeout_s=2, cancel=None)
            self.assertEqual(error.exception.code, expected)
            self.assertIsNone(transport.active_pid)

    def test_reentrancy_close_and_no_payload_in_errors(self):
        transport = self.transport('import time;time.sleep(10)')
        errors = []
        def run():
            try: transport.exchange(b'SYNTHETIC_SECRET', timeout_s=2, cancel=None)
            except ProviderError as error: errors.append(error)
        thread = threading.Thread(target=run);thread.start()
        deadline = time.monotonic()+2
        while transport.active_pid is None and time.monotonic()<deadline: time.sleep(.005)
        with self.assertRaises(ProviderError): transport.exchange(b'{}',timeout_s=1,cancel=None)
        transport.close();thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertIsNone(transport.active_pid)
        self.assertNotIn('SYNTHETIC_SECRET', repr(errors))

    def test_descendant_holding_pipe_cannot_extend_deadline(self):
        code = ("import subprocess,sys,struct;"
                "subprocess.Popen([sys.executable,'-I','-c','import time;time.sleep(3)'],stdout=sys.stdout);"
                "sys.stdout.buffer.write(struct.pack('<I',2)+b'{}');sys.stdout.buffer.flush()")
        transport = self.transport(code)
        started = time.monotonic()
        with self.assertRaises(ProviderError): transport.exchange(b'{}',timeout_s=.2,cancel=None)
        self.assertLess(time.monotonic()-started,2)
        self.assertIsNone(transport.active_pid)


@unittest.skipUnless(sys.platform == 'win32' and WORKER.is_file(), 'Build the Windows x86 worker first.')
class X86WorkerTests(unittest.TestCase):
    def test_attach_failures_reap_and_release_operation_for_next_request(self):
        from services.can.windows_worker_job import WindowsWorkerJob
        attach=WindowsWorkerJob.attach_and_resume
        request=SeedKeyRequest('test','TEST','BCM',1,b'\x01',1,3)
        for after_resume in (False,True):
            transport=ProcessWorkerTransport([str(WORKER),'--mock']);self.addCleanup(transport.close)
            def fail(job,pid):
                if after_resume: attach(job,pid)
                raise OSError('Synthetic attach failure')
            with patch.object(WindowsWorkerJob,'attach_and_resume',fail), self.assertRaises(ProviderError) as error:
                transport.exchange(encode_request(request),timeout_s=3,cancel=None)
            self.assertEqual(error.exception.code,ProviderErrorCode.UNAVAILABLE)
            self.assertIsNone(transport.active_pid)
            self.assertTrue(ProcessMockSeedKeyProvider(transport).calculate(request).mock_only)

    def test_actual_process_is_32_bit_mock_only(self):
        result = subprocess.run([str(WORKER),'--probe'],capture_output=True,timeout=3,check=True,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        self.assertEqual(json.loads(result.stdout), dict(version=1,worker_bits=32,mock_only=True,native_enabled=False))

    def test_roundtrip_matches_existing_mock_for_variable_lengths(self):
        transport = ProcessWorkerTransport([str(WORKER),'--mock'])
        self.addCleanup(transport.close)
        provider = ProcessMockSeedKeyProvider(transport)
        for length in (1,16,64):
            request = SeedKeyRequest('test','TEST','BCM',1,bytes(range(length)),length,3)
            result = provider.calculate(request)
            self.assertEqual(result, MockSeedKeyProvider().calculate(request))
            self.assertTrue(result.mock_only)
            self.assertIsNone(transport.active_pid)

    def test_native_mode_not_present_and_bad_request_is_rejected(self):
        result = subprocess.run([str(WORKER),'--native'],capture_output=True,timeout=3,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(result.stdout+result.stderr,b'')
        transport = ProcessWorkerTransport([str(WORKER),'--mock']);self.addCleanup(transport.close)
        valid = encode_request(SeedKeyRequest('test','TEST','BCM',1,b'\x01',1,3))
        for payload in (b'{}',valid.replace(b'"version":1',b'"version":true'),
                        valid.replace(b'"version":1',b'"version":1,"version":1')):
            with self.assertRaises(ProviderError): transport.exchange(payload,timeout_s=3,cancel=None)

    def test_real_x86_mock_session_cannot_prepare_live_key(self):
        from core.diagnostic_request import DiagnosticResult, DiagnosticOutcome
        from services.can.security_access_session import SecurityAccessSession, SecurityAccessBlocked
        from tests.services.test_security_seed_request import seed_request
        request = seed_request()
        session = SecurityAccessSession()
        session.start(request,'connection',0)
        session.receive(DiagnosticResult(request,DiagnosticOutcome.PASSED,b'\x67\x01\xaa'),'connection',0)
        transport = ProcessWorkerTransport([str(WORKER),'--mock']);self.addCleanup(transport.close)
        result = session.calculate_offline(ProcessMockSeedKeyProvider(transport),output_size=2)
        self.assertTrue(result.mock_only)
        with self.assertRaises(SecurityAccessBlocked):
            session.prepare_submission(request,'connection',0,authorized=True,confirmed=True)
