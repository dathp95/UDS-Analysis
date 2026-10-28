from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from core.diagnostic_request import DiagnosticResult, DiagnosticOutcome as Outcome, DiagnosticValidationError
from core.dll_resource import DllResourceMetadata, DllResourceStatus as Status
from services.seed_key_provider import MockSeedKeyProvider, SeedKeyResponse
from services.can.security_key_service import SecurityKeyService
from services.can.security_access_session import SecurityAccessSession, SecurityAccessState as State, SecurityAccessBlocked
from services.can.security_provider_gate import inspect_security_provider, ProviderReadiness
from tests.services.test_security_seed_request import seed_request


class SecurityAccessSessionTests(unittest.TestCase):
    def setUp(self):
        self.now = 10
        self.session = SecurityAccessSession(clock=lambda:self.now, ttl_s=2)
        self.request = seed_request()

    def receive(self, **changes):
        self.session.invalidate()
        self.session.start(self.request, 'connection', 0)
        result = DiagnosticResult(self.request, Outcome.PASSED, b'\x67\x01\xaa\xbb')
        self.session.receive(replace(result, **changes), 'connection', 0)

    def test_seed_lifecycle_offline_mock_and_never_live(self):
        self.receive()
        self.assertEqual(self.session.state,State.SEED_RECEIVED)
        self.session.calculate_offline(MockSeedKeyProvider(), output_size=2)
        self.assertEqual(self.session.state,State.KEY_CALCULATED)
        self.assertNotIn('aabb',repr(self.session))
        with self.assertRaises(SecurityAccessBlocked):
            self.session.prepare_submission(self.request,'connection',0,authorized=True,confirmed=True)
        self.assertNotEqual(self.session.state,State.UNLOCKED)

    def test_mismatched_contexts_cancel_and_purge(self):
        for fields, connection, epoch in ((dict(ecu_name='EPS'),'connection',0),
                                        (dict(vehicle_name='OTHER'),'connection',0),
                                        (dict(tx_id=0x682),'connection',0),
                                        (dict(generation=2),'connection',0),
                                        (dict(transaction_id='other'),'connection',0),
                                        ({},'reconnected',0),({},'connection',1)):
            self.receive()
            with self.assertRaises(SecurityAccessBlocked):
                self.session.prepare_submission(replace(self.request,**fields),connection,epoch,
                                                authorized=True,confirmed=True)
            self.assertEqual(self.session.state,State.CANCELLED)
            self.assertFalse(self.session.has_seed)

    def test_expiry_failure_and_cancellation_clear_material(self):
        self.receive();self.now+=2
        self.session.expire()
        self.assertEqual(self.session.state,State.FAILED)
        self.assertFalse(self.session.has_seed)
        for outcome, payload in ((Outcome.FAILED,b'\x7f\x27\x35'),(Outcome.TIMEOUT,None),
                                 (Outcome.ERROR,None),(Outcome.CANCELLED,None),
                                 (Outcome.PASSED,b'\x67\x02\xaa'),(Outcome.PASSED,b'\x67\x01')):
            self.receive(outcome=outcome,response_payload=payload)
            self.assertFalse(self.session.has_seed)
            self.assertIn(self.session.state,(State.FAILED,State.CANCELLED))

    def test_no_reentry_and_no_authorization_by_boolean_or_mock_result(self):
        self.session.start(self.request,'connection',0)
        with self.assertRaises(SecurityAccessBlocked): self.session.start(self.request,'connection',0)
        self.receive()
        for authorized, confirmed in ((False,True),(True,False),(True,True)):
            with self.assertRaises(SecurityAccessBlocked):
                self.session.prepare_submission(self.request,'connection',0,authorized=authorized,confirmed=confirmed)
        with self.assertRaises(DiagnosticValidationError): seed_request(uds_payload=b'\x27\x02\x11')

    def test_stale_provider_result_and_real_provider_cannot_be_promoted(self):
        session=self.session
        class SlowMock:
            def calculate(_, request, **kwargs):
                session.invalidate()
                return SeedKeyResponse(request.request_id,b'\x11\x22')
        self.receive()
        with self.assertRaises(SecurityAccessBlocked): session.calculate_offline(SlowMock(),output_size=2)
        self.assertFalse(session.has_seed)
        class ClaimedReal:
            def calculate(_, request, **kwargs): return SeedKeyResponse(request.request_id,b'\x11\x22',False)
        self.receive()
        with self.assertRaises(ValueError): session.calculate_offline(ClaimedReal(),output_size=2)
        self.assertEqual(session.state,State.FAILED)

    def test_provider_length_type_and_id_are_validated(self):
        for value in (b'',b'\x11', 'SENSITIVE',bytes(65)):
            provider=SimpleNamespace(calculate=lambda request,**_:SeedKeyResponse(request.request_id,value))
            with self.assertRaises(ValueError):
                SecurityKeyService(provider).calculate_from_response(vehicle='TEST',ecu='BCM',
                    request_payload=b'\x27\x01',response_payload=b'\x67\x01\xaa',output_size=2)

    def test_unconfirmed_seed_and_provider_exception_are_not_trusted(self):
        with self.assertRaises(DiagnosticValidationError):
            self.session.start(replace(self.request,confirmed=False),'connection',0)
        self.receive()
        class LeakingProvider:
            def calculate(_, request, **kwargs):
                raise RuntimeError('SYNTHETIC_SECRET')
        with self.assertRaises(SecurityAccessBlocked) as error:
            self.session.calculate_offline(LeakingProvider(),output_size=2)
        self.assertNotIn('SYNTHETIC_SECRET',str(error.exception))
        self.assertEqual(self.session.state,State.FAILED)


class ProviderGateTests(unittest.TestCase):
    def test_canonical_resolver_and_distinct_static_blockers(self):
        cases=[(Status.MISSING,'',None,(),ProviderReadiness.MISSING),
               (Status.MALFORMED,'',None,(),ProviderReadiness.INVALID),
               (Status.METADATA_AVAILABLE,'x64',64,('GenerateKeyEx',),ProviderReadiness.ARCH_UNSUPPORTED),
               (Status.ARCH_UNSUPPORTED,'x86',32,(),ProviderReadiness.EXPORT_UNAVAILABLE)]
        for status,machine,bits,exports,expected in cases:
            service=SimpleNamespace(resolve_ecu_dll_resource=lambda *_:DllResourceMetadata(status,'test','',machine,bits,exports))
            self.assertEqual(inspect_security_provider(service,'TEST','BCM').readiness,expected)

    def test_no_abi_no_execution_even_with_expected_digest(self):
        # Use this Python file as inert bytes: static metadata is deliberately mocked.
        path=str(Path(__file__).resolve())
        metadata=DllResourceMetadata(Status.ARCH_UNSUPPORTED,'test',path,'x86',32,('GenerateKeyEx',))
        service=SimpleNamespace(resolve_ecu_dll_resource=lambda *_:metadata)
        with patch('ctypes.CDLL',side_effect=AssertionError('No native load')):
            result=inspect_security_provider(service,'TEST','BCM')
            self.assertEqual(result.readiness,ProviderReadiness.ABI_UNVERIFIED)
            self.assertFalse(result.live_enabled)
            mismatch=inspect_security_provider(service,'TEST','BCM',expected_sha256='0'*64)
            self.assertEqual(mismatch.readiness,ProviderReadiness.DLL_MISMATCH)
            self.assertFalse(mismatch.live_enabled)
