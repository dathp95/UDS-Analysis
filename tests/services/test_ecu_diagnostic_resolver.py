import unittest
from types import SimpleNamespace
from models.ecu import ECU
from models.vehicle import Vehicle
from core.diagnostic_sequence import DiagnosticStep


class EcuDiagnosticResolverTests(unittest.TestCase):
    def resolve(self, ecus=None, step=None, name='BENCH'):
        from services.can.ecu_diagnostic_resolver import resolve_request
        service=SimpleNamespace(load_vehicle=lambda _: Vehicle('BENCH',ecus=ecus if ecus is not None else [ECU('BCM','681','0x601')]))
        return resolve_request(service,name,step or DiagnosticStep(1,'VIN','BCM','22 F1 90',expected_response='62 F1 90'),'row-id',7)

    def test_hex_ids_and_frozen_payload(self):
        result=self.resolve()
        self.assertEqual((result.tx_id,result.rx_id),(0x681,0x601))
        self.assertEqual(result.uds_payload,b'\x22\xf1\x90')
        self.assertEqual(result.generation,7)
        self.assertEqual(result.expected,b'\x62\xf1\x90')

    def test_missing_ambiguous_invalid_ids_and_extended_rejected(self):
        from core.diagnostic_request import DiagnosticValidationError
        for ecus in ([],[ECU('BCM'),ECU('BCM')],[ECU('BCM','','601')],[ECU('BCM','681','681')],
                     [ECU('BCM','1800','601')],[ECU('BCM','681','601'),ECU('OTHER','682','601')]):
            with self.assertRaises(DiagnosticValidationError): self.resolve(ecus)
        with self.assertRaises(DiagnosticValidationError): self.resolve(name='')

    def test_security_invalid_payload_and_undefined_wildcard_rejected(self):
        from core.diagnostic_request import DiagnosticValidationError
        for payload in ('27 01','27 03','','zz','34 00','10 02','10 82'):
            with self.assertRaises(DiagnosticValidationError): self.resolve(step=DiagnosticStep(1,'TEST','BCM',payload))
        with self.assertRaises(DiagnosticValidationError):
            self.resolve(step=DiagnosticStep(1,'TEST','BCM','22 F1 90',match='wildcard'))

    def test_state_changing_requires_separate_confirmation(self):
        from core.diagnostic_request import validate_send_policy, DiagnosticValidationError
        from dataclasses import replace
        request=self.resolve(step=DiagnosticStep(1,'WRITE','BCM','2E F1 90 01'))
        self.assertTrue(request.requires_confirmation)
        with self.assertRaises(DiagnosticValidationError): validate_send_policy(request)
        validate_send_policy(replace(request,confirmed=True))
        session=self.resolve(step=DiagnosticStep(1,'SESSION','BCM','10 03'))
        with self.assertRaises(DiagnosticValidationError): validate_send_policy(session)
