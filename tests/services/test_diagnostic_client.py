import unittest
from unittest.mock import patch
from dataclasses import replace
from core.diagnostic_request import DiagnosticOutcome as Outcome,DiagnosticSettings
from tests.services.test_isotp_transport import request,frame,VIN


class DiagnosticClientTests(unittest.TestCase):
    def setUp(self):
        self.now=10.0
        self.addCleanup(patch.stopall)
        patch('isotp.tools.time.perf_counter_ns',side_effect=lambda:int(self.now*1e9)).start()
        patch('isotp.protocol.time.perf_counter',side_effect=lambda:self.now).start()

    def make(self,**changes):
        from services.can.diagnostic_client import DiagnosticClient
        return DiagnosticClient(request(**changes),lambda *_:None,clock=lambda:self.now)

    def respond(self,client,text):
        client.feed(frame(text));client.poll()

    def test_prefix_exact_empty_and_negative_precedence(self):
        for fields,outcome in (({},Outcome.PASSED),({'match':'exact'},Outcome.PASSED),
                               ({'expected':b'\x62'},Outcome.PASSED),({'expected':b'\x62','match':'exact'},Outcome.FAILED),
                               ({'expected':b''},Outcome.NOT_EVALUATED)):
            client=self.make(**fields);client.poll()
            self.respond(client,'03 62 F1 90 00 00 00 00')
            self.assertEqual(client.result.outcome,outcome)
            self.assertEqual(client.result.response_payload,b'\x62\xf1\x90')
        client=self.make(expected=b'\x7f');client.poll()
        self.respond(client,'03 7F 22 31 00 00 00 00')
        self.assertEqual(client.result.outcome,Outcome.FAILED)
        self.assertEqual(client.result.nrc,0x31)

    def test_pending_final_and_original_elapsed(self):
        client=self.make();client.poll()
        self.now+=.8;self.respond(client,'03 7F 22 78 00 00 00 00')
        self.assertIsNone(client.result)
        self.now+=2;self.respond(client,'03 7F 22 78 00 00 00 00')
        self.now+=2;self.respond(client,'03 62 F1 90 00 00 00 00')
        self.assertEqual(client.result.outcome,Outcome.PASSED)
        self.assertEqual(client.result.pending_count,2)
        self.assertAlmostEqual(client.result.elapsed_s,4.8)

    def test_pending_timeout_total_budget_and_unrelated_sid(self):
        settings=DiagnosticSettings(p2_s=.1,p2_star_s=.2,total_s=.5)
        client=self.make(settings=settings);client.poll()
        for _ in range(5):
            self.now+=.09;self.respond(client,'03 7F 22 78 00 00 00 00')
        self.now+=.06;client.poll()
        self.assertEqual(client.result.outcome,Outcome.TIMEOUT)
        self.assertIsNone(client.result.response_payload)
        other=self.make(settings=settings);other.poll()
        self.now+=.11;self.respond(other,'03 7F 31 78 00 00 00 00')
        self.assertEqual(other.result.outcome,Outcome.TIMEOUT)

    def test_cancel_and_vin_reassembly(self):
        client=self.make();client.poll()
        for text in ('10 14 62 F1 90 4D 47 55','21 56 35 4A 54 4C 58 54','22 4A 39 39 39 37 34 31'):
            self.respond(client,text)
        self.assertEqual(client.result.response_payload,VIN)
        other=self.make();other.poll();other.cancel()
        self.assertEqual(other.result.outcome,Outcome.CANCELLED)

    def test_p2_limits_start_not_completion_and_late_ff_has_no_fc(self):
        settings=DiagnosticSettings(p2_s=.1,p2_star_s=.2,total_s=2)
        client=self.make(settings=settings);client.poll()
        self.now+=.09;self.respond(client,'10 14 62 F1 90 4D 47 55')
        self.now+=.02;self.respond(client,'21 56 35 4A 54 4C 58 54')
        self.now+=.01;self.respond(client,'22 4A 39 39 39 37 34 31')
        self.assertEqual(client.result.outcome,Outcome.PASSED)
        sent=[]
        from services.can.diagnostic_client import DiagnosticClient
        late=DiagnosticClient(request(settings=settings),lambda *args:sent.append(args),clock=lambda:self.now)
        late.poll();self.now+=.11
        self.respond(late,'10 14 62 F1 90 4D 47 55')
        self.assertEqual(late.result.outcome,Outcome.TIMEOUT)
        self.assertEqual(len(sent),1)

    def test_echo_matching_and_incomplete_tx_cannot_pass(self):
        client=self.make(expected=b'\x62');client.poll()
        self.respond(client,'03 62 F1 91 00 00 00 00')
        self.assertIsNone(client.result)
        self.respond(client,'03 62 F1 90 00 00 00 00')
        self.assertEqual(client.result.outcome,Outcome.PASSED)
        other=self.make(uds_payload=b'\x2e\xf1\x90'+bytes(20),expected=b'\x6e',confirmed=True);other.poll()
        self.respond(other,'03 6E F1 90 00 00 00 00')
        self.assertIsNone(other.result)
        self.assertTrue(other.engine.transmitting)

    def test_cancel_racing_response_wins(self):
        client=self.make();client.poll()
        def receive():
            client.cancelled.set()
            return b'\x62\xf1\x90'
        with patch.object(client.engine,'receive',side_effect=receive): client.poll()
        self.assertEqual(client.result.outcome,Outcome.CANCELLED)
