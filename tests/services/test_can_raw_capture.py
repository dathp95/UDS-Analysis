import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import can
from services.can import VectorBackend, CANConfig


class RawCaptureTests(unittest.TestCase):
    def backend(self, channel=0):
        bus=SimpleNamespace(send=lambda *a,**k:None,recv=lambda **k:None,shutdown=lambda:None)
        backend=VectorBackend(can_module=SimpleNamespace(Bus=lambda **k:bus,Message=can.Message))
        backend.fn_open(CANConfig('vector',channel,500000))
        self.addCleanup(backend.fn_close)
        return backend,bus

    def test_session_sequence_channel_timestamp_and_echo(self):
        for channel in (0,1):
            backend,bus=self.backend(channel)
            tx=backend.fn_send_frame(0x681,b'\x03\x22\xf1\x90')
            bus.recv=lambda **k:can.Message(timestamp=tx.wall_timestamp_s+.001,arbitration_id=0x681,
                data=tx.data,is_extended_id=False,is_rx=False,channel=channel)
            echo=backend.fn_receive_frame()
            self.assertEqual((tx.channel,echo.channel),(channel,channel))
            self.assertEqual(echo.source_channel,channel)
            self.assertEqual(echo.echo_of_sequence,tx.sequence)
            self.assertEqual(echo.session_id,tx.session_id)
            self.assertGreater(echo.sequence,tx.sequence)
            self.assertAlmostEqual(echo.timestamp_s-tx.timestamp_s,.001,places=4)

    def test_missing_clock_fallback_and_backward_time_explicit(self):
        backend,bus=self.backend()
        now=time.time()
        def read(stamp):
            bus.recv=lambda **k:can.Message(timestamp=stamp,arbitration_id=0x760,data=[1],is_extended_id=False)
            return backend.fn_receive_frame()
        first=read(now)
        second=read(now-.01)
        self.assertEqual(second.source_timestamp_s,now-.01)
        self.assertEqual(second.wall_timestamp_s,first.wall_timestamp_s)
        self.assertIn('clamped',second.timestamp_source)
        missing=read(0)
        self.assertIn('fallback',missing.timestamp_source)
        self.assertGreater(missing.wall_timestamp_s,1_000_000_000)

    def test_unexpected_source_channel_is_rejected_and_reconnect_has_new_generation(self):
        backend,bus=self.backend()
        first=backend.fn_send_frame(0x681,b'\x01')
        bus.recv=lambda **k:can.Message(timestamp=time.time(),arbitration_id=0x760,data=[1],is_extended_id=False,channel=99)
        with self.assertRaisesRegex(ValueError,'mapping is uncertain'): backend.fn_receive_frame()
        backend.fn_close();backend.fn_open(CANConfig('vector',0,500000))
        second=backend.fn_send_frame(0x681,b'\x01')
        self.assertNotEqual(first.session_id,second.session_id)
        self.assertEqual(second.sequence,1)

    def test_nonstandard_dlc_and_data_normalized_without_crash(self):
        backend, bus = self.backend()
        # Case 1: DLC > 8 (e.g. 15 on Classical CAN)
        bus.recv = lambda **k: can.Message(
            timestamp=time.time(), arbitration_id=0x760, data=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            dlc=15, is_extended_id=False
        )
        frame1 = backend.fn_receive_frame()
        self.assertIsNotNone(frame1)
        self.assertLessEqual(frame1.dlc, 8)
        self.assertLessEqual(len(frame1.data), frame1.dlc)

        # Case 2: DLC > 8 (e.g. 12 on Classical CAN)
        bus.recv = lambda **k: can.Message(
            timestamp=time.time(), arbitration_id=0x761, data=[1, 2, 3, 4, 5, 6, 7, 8],
            dlc=12, is_extended_id=False
        )
        frame2 = backend.fn_receive_frame()
        self.assertIsNotNone(frame2)
        self.assertEqual(frame2.dlc, 8)
        self.assertEqual(len(frame2.data), 8)
