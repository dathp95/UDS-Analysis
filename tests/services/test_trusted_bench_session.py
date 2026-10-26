import unittest
from dataclasses import replace
from core.diagnostic_request import DiagnosticValidationError,validate_send_policy
from services.can import CANService,CANConfig
from tests.services.test_can_service import FakeCANBackend
from tests.services.test_isotp_transport import request
from core.bench_authorization import BenchAuthorizationContext


class TrustedBenchTests(unittest.TestCase):
    def setUp(self):
        self.backend=FakeCANBackend();self.backend.capture_session_id='connection-1'
        self.service=CANService(self.backend)
        self.service.fn_connect(CANConfig('vector',0,500000))
        self.addCleanup(self.service.fn_disconnect)

    def enable(self,authorized=True):
        self.service.fn_disconnect()
        self.service.fn_connect(CANConfig('vector',0,500000,
            bench_context=BenchAuthorizationContext('bench-A',authorized=authorized)))
        return self.service.trusted_bench

    def test_explicit_approval_connection_and_exact_payload_scope(self):
        self.assertIsNone(self.enable(authorized=False))
        with self.assertRaises(ValueError): BenchAuthorizationContext('',authorized=True)
        with self.assertRaises(ValueError):
            self.service.fn_connect(CANConfig('vector',0,500000,bench_context='not-a-context'))
        for payload in ('10 01','10 03','14 FF FF FF'):
            req=request(uds_payload=bytes.fromhex(payload))
            self.assertIsNone(self.service.fn_confirm_trusted_request(req))
            self.enable()
            confirmed=self.service.fn_confirm_trusted_request(req)
            self.assertTrue(confirmed.confirmed)
            self.assertTrue(confirmed.bench_authorization_id)
            validate_send_policy(confirmed)
            self.service.fn_begin_diagnostic(confirmed);self.service.fn_end_diagnostic(confirmed.transaction_id)
            self.service.fn_revoke_trusted_bench()

    def test_restricted_services_and_payload_variants_require_manual_confirmation(self):
        self.enable()
        for text in ('11 01','2E F1 90 01','31 01 12 34','85 02','10 04','10 81','10 03 00','14 00 00 00'):
            req=request(uds_payload=bytes.fromhex(text))
            self.assertIsNone(self.service.fn_confirm_trusted_request(req),text)
            with self.assertRaises(DiagnosticValidationError): validate_send_policy(req)
        with self.assertRaises(DiagnosticValidationError): request(uds_payload=bytes.fromhex('27 01'))
        other=request(vehicle_name='OTHER',uds_payload=bytes.fromhex('10 03'))
        self.assertIsNotNone(self.service.fn_confirm_trusted_request(other))

    def test_stale_forged_and_reconnected_authorizations_rejected_before_tx(self):
        self.enable()
        req=self.service.fn_confirm_trusted_request(request(uds_payload=bytes.fromhex('10 03')))
        forged=replace(req,bench_authorization_id='not-issued')
        with self.assertRaises(DiagnosticValidationError): self.service.fn_begin_diagnostic(forged)
        with self.assertRaises(DiagnosticValidationError): replace(req,uds_payload=bytes.fromhex('11 01'))
        self.service.fn_revoke_trusted_bench()
        with self.assertRaises(DiagnosticValidationError): self.service.fn_begin_diagnostic(req)
        self.enable()
        req=self.service.fn_confirm_trusted_request(request(uds_payload=bytes.fromhex('10 03')))
        self.service.fn_disconnect()
        self.assertIsNone(self.service.trusted_bench)
        self.backend.capture_session_id='connection-2'
        self.service.fn_connect(CANConfig('vector',0,500000))
        with self.assertRaises(DiagnosticValidationError): self.service.fn_begin_diagnostic(req)
        self.assertIsNone(self.service.fn_confirm_trusted_request(request(uds_payload=bytes.fromhex('10 03'))))
        fresh=CANService(self.backend)
        self.assertIsNone(fresh.trusted_bench)
