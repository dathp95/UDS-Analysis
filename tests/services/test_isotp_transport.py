import unittest
from dataclasses import replace
from unittest.mock import patch
from core.diagnostic_request import DiagnosticRequest,DiagnosticSettings
from core.can_interface_view import CanFrameView
from services.can.isotp_transport import IsoTpTransport

VIN=bytes.fromhex('62 F1 90 4D 47 55 56 35 4A 54 4C 58 54 4A 39 39 39 37 34 31')


def request(**changes):
    return replace(DiagnosticRequest('tx','row',1,'BENCH','BCM',0x681,0x601,b'\x22\xf1\x90',b'\x62\xf1\x90'),**changes)


def frame(text,can_id=0x601):
    data=bytes.fromhex(text)
    return CanFrameView(0.0,'RX',can_id,len(data),data)


class IsoTpTests(unittest.TestCase):
    def setUp(self):
        self.now=10.0
        self.addCleanup(patch.stopall)
        patch('isotp.tools.time.perf_counter_ns',side_effect=lambda:int(self.now*1e9)).start()
        patch('isotp.protocol.time.perf_counter',side_effect=lambda:self.now).start()
        self.sent=[]
        self.engine=IsoTpTransport(request(),lambda can_id,data:self.sent.append((can_id,data)))
        self.engine.process()

    def test_sf_and_multiframe_vin_flow_control(self):
        self.assertEqual(self.sent[0],(0x681,bytes.fromhex('03 22 F1 90 00 00 00 00')))
        self.engine.feed(frame('10 14 62 F1 90 4D 47 55'));self.engine.process()
        self.assertEqual(self.sent[-1],(0x681,bytes.fromhex('30 00 00 00 00 00 00 00')))
        self.engine.feed(frame('21 56 35 4A 54 4C 58 54'))
        self.engine.feed(frame('22 4A 39 39 39 37 34 31'));self.engine.process()
        self.assertEqual(self.engine.receive(),VIN)

    def test_unrelated_ff_never_generates_flow_control(self):
        self.engine.feed(frame('10 14 62 F1 90 4D 47 55',0x602))
        self.engine.feed(frame('10 14 59 02 00 00 00 00'))
        self.engine.feed(frame('10 14 62 F1 91 4D 47 55'))
        self.engine.process()
        self.assertEqual(len(self.sent),1)
        self.assertIsNone(self.engine.receive())

    def test_bad_sequence_and_malformed_sf(self):
        self.engine.feed(frame('10 14 62 F1 90 4D 47 55'));self.engine.process()
        self.engine.feed(frame('23 01 02 03 04 05 06 07'));self.engine.process()
        self.assertIsNotNone(self.engine.error)
        engine=IsoTpTransport(request(),lambda *_:None)
        engine.process();engine.feed(frame('07 62 F1'));engine.process()
        self.assertIsNotNone(engine.error)

    def test_multiframe_tx_wait_fc_bs_stmin_and_counter_wrap(self):
        sent=[]
        req=request(uds_payload=b'\x2e\xf1\x90'+bytes(range(150)),confirmed=True)
        engine=IsoTpTransport(req,lambda _,data:sent.append(data));engine.process()
        self.assertEqual(len(sent),1)
        self.assertEqual(sent[0][0]>>4,1)
        engine.feed(frame('30 02 0A 00 00 00 00 00'));engine.process()
        self.assertEqual(len(sent),1)
        for _ in range(2): self.now+=.011;engine.process()
        self.assertEqual([x[0] for x in sent],[0x10,0x21,0x22])
        self.now+=.1;engine.process();self.assertEqual(len(sent),3)
        engine.feed(frame('30 00 00 00 00 00 00 00'))
        for _ in range(20): self.now+=.021;engine.process()
        self.assertFalse(engine.transmitting)
        self.assertIn(0x20,[x[0] for x in sent])
        joined=sent[0][2:]+b''.join(x[1:] for x in sent[1:])
        self.assertEqual(joined[:len(req.uds_payload)],req.uds_payload)

    def test_fc_timeout_overflow_wait_limit_and_rx_timeout(self):
        for control in (None,'32 00 00','31 00 00'):
            engine=IsoTpTransport(request(uds_payload=b'\x2e'+bytes(20),confirmed=True),lambda *_:None)
            engine.process()
            if control:
                for _ in range(4): engine.feed(frame(control));engine.process()
            else:
                self.now+=1.01;engine.process()
            self.assertIsNotNone(engine.error)
        self.engine.feed(frame('10 14 62 F1 90 4D 47 55'));self.engine.process()
        self.now+=1.01;self.engine.process()
        self.assertTrue(self.engine.timed_out)
