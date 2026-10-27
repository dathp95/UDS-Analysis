import unittest
from dataclasses import replace
from unittest.mock import patch

from core.diagnostic_request import (DiagnosticValidationError, DiagnosticOutcome as Outcome,
    DiagnosticSettings, TrustedBenchAuthorization, response_belongs_to_request, validate_send_policy)
from tests.services.test_isotp_transport import request, frame

SEED_REQUEST = b'\x27\x01'


def seed_request(**changes):
    fields = dict(uds_payload=SEED_REQUEST, expected=b'\x67\x01', confirmed=True)
    fields.update(changes)
    return request(**fields)


class SecuritySeedPolicyTests(unittest.TestCase):
    def test_exact_seed_admission_and_explicit_manual_authorization(self):
        admitted = seed_request(confirmed=False)
        self.assertTrue(admitted.requires_confirmation)
        with self.assertRaises(DiagnosticValidationError): validate_send_policy(admitted)
        validate_send_policy(replace(admitted, confirmed=True))
        for payload in (b'\x27', b'\x27\x00', b'\x27\x02', b'\x27\x03',
                        b'\x27\x81', b'\x27\xff', b'\x27\x01\x00', b'\x27\x02\x00\x00'):
            with self.subTest(payload=payload), self.assertRaises(DiagnosticValidationError):
                seed_request(uds_payload=payload)

    def test_correlation_requires_exact_echo_and_nonempty_seed(self):
        req = seed_request()
        for payload in (b'\x67\x01\x00', b'\x67\x01\xab\xcd', b'\x67\x01'+bytes(64)):
            self.assertTrue(response_belongs_to_request(req, payload))
        for payload in (b'', b'\x67', b'\x67\x01', b'\x67\x02\xab\xcd',
                        b'\x67\x03\xab\xcd', b'\x67\x81\xab\xcd', b'\x62\xf1\x90'):
            self.assertFalse(response_belongs_to_request(req, payload))
        for nrc in (0x7F,0x22,0x24,0x33,0x35,0x36,0x37,0x78):
            self.assertTrue(response_belongs_to_request(req, bytes((0x7F,0x27,nrc))))
        self.assertFalse(response_belongs_to_request(req, b'\x7f\x22\x31'))

    def test_seed_does_not_broaden_bench_grant_or_other_services(self):
        grant = TrustedBenchAuthorization('auth','connection','bench')
        self.assertFalse(grant.permits(seed_request(), 'connection'))
        with self.assertRaises(DiagnosticValidationError): seed_request(bench_authorization_id='auth')
        for payload in ('10 01','10 03','14 FF FF FF','11 01','2E F1 90 00','31 01 12 34','85 02'):
            req = request(uds_payload=bytes.fromhex(payload))
            self.assertTrue(req.requires_confirmation)
            with self.assertRaises(DiagnosticValidationError): validate_send_policy(req)
        self.assertFalse(request(uds_payload=b'\x22\xf1\x90').requires_confirmation)
        for payload in ('10 02','10 82','34 00'):
            with self.assertRaises(DiagnosticValidationError): request(uds_payload=bytes.fromhex(payload))


class SecuritySeedTransportTests(unittest.TestCase):
    def setUp(self):
        self.now = 10.0
        self.addCleanup(patch.stopall)
        patch('isotp.tools.time.perf_counter_ns', side_effect=lambda: int(self.now*1e9)).start()
        patch('isotp.protocol.time.perf_counter', side_effect=lambda: self.now).start()
        self.sent = []

    def client(self, **changes):
        from services.can.diagnostic_client import DiagnosticClient
        client = DiagnosticClient(seed_request(**changes), lambda *args: self.sent.append(args), clock=lambda: self.now)
        client.poll()
        return client

    def feed(self, client, data):
        client.feed(frame(bytes(data).hex(' ')))
        client.poll()

    def single(self, client, payload, padding=b'\0'):
        data = bytes((len(payload),)) + payload
        self.feed(client, data + padding*(8-len(data)))

    def multiple(self, client, payload):
        size = len(payload)
        self.feed(client, bytes((0x10 | size >> 8,size & 0xFF))+payload[:6])
        for index, offset in enumerate(range(6,size,7),1):
            data = bytes((0x20 | index & 0xF,))+payload[offset:offset+7]
            self.feed(client, data+bytes(8-len(data)))

    def test_single_frame_seed_lengths_and_expectation_semantics(self):
        for length in (1,2,5):
            client = self.client()
            payload = b'\x67\x01'+bytes(range(length))
            with self.assertNoLogs(): self.single(client,payload)
            self.assertEqual(client.result.outcome, Outcome.PASSED)
            self.assertEqual(client.result.response_payload, payload)
        for fields, outcome in ((dict(match='exact'),Outcome.FAILED),
                                (dict(expected=b''),Outcome.NOT_EVALUATED),
                                (dict(expected=b'\x67\x01\xff'),Outcome.FAILED)):
            client=self.client(**fields);self.single(client,b'\x67\x01\xab\xcd')
            self.assertEqual(client.result.outcome,outcome)

    def test_multiframe_full_seed_and_maximum_existing_payload(self):
        for length in (6,16,64,4093):
            client=self.client();before=len(self.sent)
            payload=b'\x67\x01'+bytes(index % 256 for index in range(length))
            self.multiple(client,payload)
            self.assertEqual(client.result.outcome,Outcome.PASSED)
            self.assertEqual(client.result.response_payload,payload)
            self.assertEqual(self.sent[before][1][0],0x30)

    def test_missing_seed_padding_wrong_echo_and_wrong_can_id_cannot_pass(self):
        client=self.client()
        self.single(client,b'\x67\x01',padding=b'\xab')  # Padding must never become seed.
        self.single(client,b'\x67\x03\xab\xcd')
        self.single(client,b'\x67\x02\xab\xcd')
        client.feed(frame('04 67 01 AB CD 00 00 00',can_id=0x602));client.poll()
        self.assertIsNone(client.result)
        before=len(self.sent)
        self.feed(client,bytes.fromhex('10 12 67 03 01 02 03 04'))
        self.assertEqual(len(self.sent),before)  # No FC for a different security level.
        self.single(client,b'\x67\x01\xab\xcd')
        self.assertEqual(client.result.outcome,Outcome.PASSED)
        malformed=self.client();self.feed(malformed,b'\x04\x67\x01')
        self.assertEqual(malformed.result.outcome,Outcome.ERROR)
        corrupted=self.client();self.feed(corrupted,bytes.fromhex('10 12 67 01 00 01 02 03'))
        self.feed(corrupted,bytes.fromhex('23 04 05 06 07 08 09 0A'))
        self.assertEqual(corrupted.result.outcome,Outcome.ERROR)

    def test_missing_seed_times_out_and_terminal_negatives_remain_failed(self):
        client=self.client();self.single(client,b'\x67\x01')
        self.now+=1.01;client.poll()
        self.assertEqual(client.result.outcome,Outcome.TIMEOUT)
        self.assertIsNone(client.result.response_payload)
        for nrc in (0x7F,0x22,0x24,0x33,0x35,0x36,0x37):
            client=self.client();self.single(client,bytes((0x7F,0x27,nrc)))
            self.assertEqual(client.result.outcome,Outcome.FAILED)
            self.assertEqual(client.result.nrc,nrc)

    def test_pending_then_delayed_multiframe_seed_and_elapsed_time(self):
        settings=DiagnosticSettings(p2_s=.1,p2_star_s=.3,total_s=2)
        client=self.client(settings=settings);start=self.now
        for interval in (.08,.15):
            self.now+=interval;self.single(client,b'\x7f\x27\x78');self.assertIsNone(client.result)
        self.now+=.2;payload=b'\x67\x01'+bytes(range(16));self.multiple(client,payload)
        self.assertEqual(client.result.outcome,Outcome.PASSED)
        self.assertEqual(client.result.pending_count,2)
        self.assertAlmostEqual(client.result.elapsed_s,self.now-start)

    def test_pending_timeout_unrelated_negative_and_cancelled_late_response(self):
        settings=DiagnosticSettings(p2_s=.1,p2_star_s=.2,total_s=.5)
        client=self.client(settings=settings);self.single(client,b'\x7f\x27\x78')
        self.now+=.21;client.poll()
        self.assertEqual(client.result.outcome,Outcome.TIMEOUT)
        self.assertEqual(client.result.pending_count,1)
        other=self.client(settings=settings);self.single(other,b'\x7f\x22\x31')
        self.now+=.11;other.poll()
        self.assertEqual(other.result.outcome,Outcome.TIMEOUT)
        cancelled=self.client();cancelled.cancel();self.single(cancelled,b'\x67\x01\xab\xcd')
        self.assertEqual(cancelled.result.outcome,Outcome.CANCELLED)
        self.assertIsNone(cancelled.result.response_payload)
