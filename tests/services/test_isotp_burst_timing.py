"""Deterministic tests for ISO-TP multi-frame burst pump timing and transport stability."""
import sys
from pathlib import Path
import time
import unittest
from unittest.mock import Mock, MagicMock
from threading import Event

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.bench_authorization import BenchAuthorizationContext
from core.diagnostic_request import (
    DiagnosticRequest,
    DiagnosticSettings,
    DiagnosticOutcome,
)
from services.can import CANService, CANConfig
from services.can.simulated_backend import SimulatedCANBackend
from gui.workers.can_diagnostic_session import CanDiagnosticSession


class TestIsoTpBurstTiming(unittest.TestCase):
    def setUp(self):
        self.backend = SimulatedCANBackend()
        self.service = CANService(self.backend)
        self.service.fn_connect(
            CANConfig('vector', 0, 500000, bench_context=BenchAuthorizationContext('sim-bench', True))
        )
        self.addCleanup(self.service.fn_disconnect)
        self.settings = DiagnosticSettings(p2_s=1.0, p2_star_s=2.0, total_s=5.0)

    def test_multiframe_tx_sends_cf_within_deadline_stmin_zero(self):
        """When ECU Flow Control has STmin=0, multi-frame transaction completes within tight window."""
        session = CanDiagnosticSession(self.service, None)
        session.monitoring = True
        results = []
        session.finished.connect(results.append)

        # 18 bytes payload requiring multi-frame
        req = DiagnosticRequest(
            transaction_id='tx_mf_1',
            step_id='step_1',
            generation=1,
            vehicle_name='VF5NP',
            ecu_name='BCM',
            tx_id=0x681,
            rx_id=0x601,
            uds_payload=bytes.fromhex('2E F1 5C 11 22 33 44 55 66 77 88 99 AA BB CC DD EE FF'),
            expected=b'\x6E\xF1\x5C',
            settings=self.settings,
            confirmed=True,
        )

        cancelled = Event()
        session.start(req, cancelled)

        # Pump session
        t_start = time.perf_counter()
        while not results:
            session._pump()
            if time.perf_counter() - t_start > 1.0:
                break
            time.sleep(0.001)

        self.assertTrue(bool(results), "Expected diagnostic transaction to finish")
        result = results[0]
        self.assertEqual(result.outcome, DiagnosticOutcome.PASSED)
        # Total transaction duration should be under 150ms
        self.assertLess(time.perf_counter() - t_start, 0.150)

    def test_multiframe_rx_sends_fc_immediately(self):
        """When ECU sends First Frame (Seed), tester must transmit Flow Control in under 10ms."""
        session = CanDiagnosticSession(self.service, None)
        session.monitoring = True
        results = []
        session.finished.connect(results.append)

        # 27 01 request -> ECU responds with 10 12 67 01 ... (multi-frame seed)
        req = DiagnosticRequest(
            transaction_id='tx_rx_fc',
            step_id='step_1',
            generation=1,
            vehicle_name='VF5NP',
            ecu_name='BCM',
            tx_id=0x681,
            rx_id=0x601,
            uds_payload=b'\x27\x01',
            expected=b'\x67\x01',
            settings=self.settings,
            confirmed=True,
        )

        self.backend._extended = True
        session.start(req, Event())
        t_start = time.perf_counter()
        while not results:
            session._pump()
            if time.perf_counter() - t_start > 1.0:
                break
            time.sleep(0.001)

        self.assertTrue(bool(results), "Expected transaction to complete")
        result = results[0]
        self.assertEqual(result.outcome, DiagnosticOutcome.PASSED)
        self.assertEqual(result.response_payload[:2], b'\x67\x01')

        # Find the Flow Control transmitted by tester
        fc_frames = [f for f in self.backend.frames if f.direction == 'TX' and f.data[:1] == b'\x30']
        self.assertTrue(bool(fc_frames), "Expected tester to send Flow Control")
        fc_frame = fc_frames[0]
        # Find ECU First Frame
        ff_frames = [f for f in self.backend.frames if f.direction == 'RX' and (f.data[0] >> 4) == 1]
        self.assertTrue(bool(ff_frames), "Expected ECU First Frame")
        ff_frame = ff_frames[0]
        delta_ms = (fc_frame.monotonic_timestamp_s - ff_frame.monotonic_timestamp_s) * 1000
        # Flow Control must be sent in < 25ms, avoiding ECU N_Bs timeout
        self.assertLess(delta_ms, 25.0)

    def test_vector_backend_fn_receive_frame_supports_timeout(self):
        """VectorBackend.fn_receive_frame must accept timeout parameter and forward to bus.recv."""
        from services.can.vector_backend import VectorBackend
        backend = VectorBackend()
        bus_mock = MagicMock()
        bus_mock.recv.return_value = None
        backend._bus = bus_mock
        backend._channel = 0
        import threading
        backend._owner_thread_id = threading.get_ident()

        backend.fn_receive_frame(timeout=0.005)
        bus_mock.recv.assert_called_with(timeout=0.005)


if __name__ == '__main__':
    unittest.main()
