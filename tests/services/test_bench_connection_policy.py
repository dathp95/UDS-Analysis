import unittest
from dataclasses import replace
from threading import Event,Thread
from unittest.mock import Mock
from core.diagnostic_request import DiagnosticValidationError,DiagnosticCancelled,validate_send_policy
from services.can import CANService,CANConfig
from tests.services.test_can_service import FakeCANBackend
from tests.services.test_isotp_transport import request


class BenchConnectionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.backend=FakeCANBackend();self.backend.capture_session_id='connection-1'
        self.service=CANService(self.backend)
        self.addCleanup(self.service.fn_disconnect)

    def context(self,name='bench-A',authorized=True):
        from core.bench_authorization import BenchAuthorizationContext
        return BenchAuthorizationContext(name,authorized=authorized)

    def test_only_explicit_connection_config_authorizes_exact_allowlist(self):
        self.service.fn_connect(CANConfig('vector',0,500000))
        self.assertIsNone(self.service.fn_confirm_trusted_request(request(uds_payload=b'\x10\x03')))
        self.service.fn_disconnect()
        self.service.fn_connect(CANConfig('vector',0,500000,bench_context=self.context()))
        for payload in ('10 01','10 03','14 FF FF FF'):
            req=self.service.fn_confirm_trusted_request(request(uds_payload=bytes.fromhex(payload)))
            self.assertTrue(req.confirmed);validate_send_policy(req)
            self.service.fn_begin_diagnostic(req);self.service.fn_end_diagnostic(req.transaction_id)

    def test_context_change_revokes_without_implicitly_granting_new_context(self):
        self.service.fn_connect(CANConfig('vector',0,500000,bench_context=self.context()))
        old=self.service.fn_confirm_trusted_request(request(uds_payload=b'\x10\x03'))
        self.service.fn_configure_bench_context(self.context())
        self.assertIsNotNone(self.service.trusted_bench)
        self.service.fn_configure_bench_context(self.context('bench-B'))
        self.assertIsNone(self.service.trusted_bench)
        with self.assertRaises(DiagnosticValidationError): self.service.fn_begin_diagnostic(old)
        self.assertIsNone(self.service.fn_confirm_trusted_request(request(uds_payload=b'\x10\x03')))

    def test_unapproved_config_and_other_services_do_not_gain_authority(self):
        self.service.fn_connect(CANConfig('vector',0,500000,bench_context=self.context(authorized=False)))
        self.assertIsNone(self.service.trusted_bench)
        self.service.fn_disconnect()
        self.service.fn_connect(CANConfig('vector',0,500000,bench_context=self.context()))
        for text in ('11 01','2E F1 90 01','31 01 12 34','85 02','10 81','10 03 00','14 00 00 00'):
            req=request(uds_payload=bytes.fromhex(text))
            self.assertIsNone(self.service.fn_confirm_trusted_request(req))
            with self.assertRaises(DiagnosticValidationError): self.service.fn_begin_diagnostic(req)
        with self.assertRaises(DiagnosticValidationError): request(uds_payload=b'\x27\x01')

    def test_expiry_generation_forgery_and_process_restart(self):
        self.service.fn_connect(CANConfig('vector',0,500000,bench_context=self.context()))
        req=self.service.fn_confirm_trusted_request(request(uds_payload=b'\x10\x03'))
        with self.assertRaises(DiagnosticValidationError): self.service.fn_begin_diagnostic(replace(req,bench_authorization_id='forged'))
        self.service.fn_disconnect();self.assertIsNone(self.service.trusted_bench)
        self.backend.capture_session_id='connection-2'
        self.service.fn_connect(CANConfig('vector',0,500000))
        with self.assertRaises(DiagnosticValidationError): self.service.fn_begin_diagnostic(req)
        self.assertIsNone(self.service.trusted_bench)
        self.assertIsNone(CANService(self.backend).trusted_bench)

    def test_missing_generation_cannot_issue_grant_even_with_approved_config(self):
        for generation in ('',None,True):
            self.backend.capture_session_id=generation
            self.service.fn_connect(CANConfig('vector',0,500000,bench_context=self.context()))
            self.assertIsNone(self.service.trusted_bench)
            self.assertIsNone(self.service.fn_confirm_trusted_request(request(uds_payload=b'\x10\x03')))
            self.service.fn_disconnect()

    def test_context_change_while_connecting_cancels_pending_authorization(self):
        entered,release=Event(),Event()
        original=self.backend.fn_open
        def slow_open(config):
            entered.set();release.wait(2);original(config)
        self.backend.fn_open=slow_open
        worker=Thread(target=self.service.fn_connect,args=(CANConfig('vector',0,500000,bench_context=self.context()),))
        worker.start()
        try:
            self.assertTrue(entered.wait(1))
            self.service.fn_configure_bench_context(self.context('bench-B'))
        finally:
            release.set();worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertTrue(self.service.fn_is_connected())
        self.assertIsNone(self.service.trusted_bench)

    def test_revocation_between_admission_and_tx_blocks_actual_frame(self):
        self.backend.fn_send_frame=Mock()
        self.service.fn_connect(CANConfig('vector',0,500000,bench_context=self.context()))
        req=self.service.fn_confirm_trusted_request(request(uds_payload=b'\x10\x03'))
        self.service.fn_begin_diagnostic(req)
        try:
            self.service.fn_configure_bench_context(self.context('bench-B',authorized=False))
            with self.assertRaises(DiagnosticCancelled): self.service.fn_send_diagnostic_frame(req.tx_id,b'\x02\x10\x03')
            self.backend.fn_send_frame.assert_not_called()
        finally: self.service.fn_end_diagnostic(req.transaction_id)

    def test_revoke_while_connecting_is_not_undone_by_completion(self):
        entered,release=Event(),Event()
        original=self.backend.fn_open
        def slow_open(config):
            entered.set();release.wait(2);original(config)
        self.backend.fn_open=slow_open
        worker=Thread(target=self.service.fn_connect,args=(CANConfig('vector',0,500000,bench_context=self.context()),))
        worker.start()
        try:
            self.assertTrue(entered.wait(1))
            self.service.fn_revoke_trusted_bench()
        finally:
            release.set();worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertTrue(self.service.fn_is_connected())
        self.assertIsNone(self.service.trusted_bench)

    def test_revocation_serializes_with_bench_tx_without_locking_snapshot(self):
        self.service.fn_connect(CANConfig('vector',0,500000,bench_context=self.context()))
        req=self.service.fn_confirm_trusted_request(request(uds_payload=b'\x10\x03'))
        entered,release,revoked,snapshot_read=Event(),Event(),Event(),Event()
        order=[]
        def send(*_):
            entered.set();release.wait(2);order.append('TX')
        self.backend.fn_send_frame=send
        def owner():
            self.service.fn_begin_diagnostic(req)
            try: self.service.fn_send_diagnostic_frame(req.tx_id,b'\x02\x10\x03')
            finally: self.service.fn_end_diagnostic(req.transaction_id)
        def revoke():
            self.service.fn_revoke_trusted_bench();order.append('REVOKED');revoked.set()
        def read_snapshot():
            self.service.snapshot;snapshot_read.set()
        tx=Thread(target=owner);tx.start();self.assertTrue(entered.wait(1))
        revoker=Thread(target=revoke);reader=Thread(target=read_snapshot)
        revoker.start();reader.start()
        try:
            completed_early=revoked.wait(.1)
            readable=snapshot_read.wait(.2)
        finally:
            release.set();tx.join(2);revoker.join(2);reader.join(2)
        self.assertFalse(completed_early)
        self.assertTrue(readable)
        self.assertEqual(order,['TX','REVOKED'])
