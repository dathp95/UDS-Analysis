import unittest
from threading import Event, Thread
from unittest.mock import Mock, patch
from types import SimpleNamespace

from services.can import CANConfig, CANConnectionError, CANService, VectorBackend
from tests.services.test_can_service import FakeCANBackend


class CANConnectionTests(unittest.TestCase):
    def test_invalid_or_missing_hardware_identity_is_rejected(self):
        from services.can import CANValidationError
        backend = FakeCANBackend()
        service = CANService(backend)
        for config in (CANConfig("vector", 0, 500000, channel_index=8),
                       CANConfig("vector", 0, 500000, serial=123),
                       CANConfig("vector", 0, 500000, serial=123, channel_index=-1),
                       CANConfig("vector", 0, 500000.0),
                       CANConfig("vector", 0, 500000, fd=True)):
            with self.assertRaises(CANValidationError):
                service.fn_connect(config)
        self.assertIsNone(backend.opened_config)

    def test_missing_dependency_preserves_cause_and_clean_error_state(self):
        from services.can import CANConnectionState as State
        service = CANService(VectorBackend())
        with patch("services.can.vector_backend.import_module", side_effect=ImportError("missing")):
            with self.assertRaises(CANConnectionError) as raised:
                service.fn_connect(CANConfig("vector", 0, 500000))
        self.assertIn("python-can", str(raised.exception))
        self.assertIsInstance(raised.exception.__cause__, ImportError)
        self.assertEqual(service.snapshot.state, State.ERROR)
        service.fn_disconnect()
        self.assertEqual(service.snapshot.state, State.DISCONNECTED)

    def test_error_codes_are_preferred_to_arbitrary_text(self):
        for code, expected in ((129, "hardware"), (111, "channel"), (158, "busy"), (201, "Driver")):
            error = RuntimeError("unrelated text")
            error.error_code = code
            self.assertIn(expected, VectorBackend._translate_error(error))

    def test_rediscovery_requirement_cannot_be_cleared_by_disconnect(self):
        from services.can import CANConnectionState as State
        backend = FakeCANBackend()
        service = CANService(backend)
        original = backend.fn_open
        backend.fn_open = Mock(side_effect=CANConnectionError("hardware lost", rediscovery_required=True))
        config = CANConfig("vector", 0, 500000)
        with self.assertRaises(CANConnectionError):
            service.fn_connect(config)
        service.fn_disconnect()
        self.assertEqual(service.snapshot.state, State.DISCONNECTED)
        with self.assertRaises(CANConnectionError):
            service.fn_connect(config)
        service.fn_refresh()
        backend.fn_open = original
        service.fn_connect(config)
        service.fn_disconnect()

    def test_connect_and_refresh_are_rejected_during_disconnect(self):
        from services.can import CANConnectionState as State, CANDiscoveryError
        backend = FakeCANBackend()
        service = CANService(backend)
        config = CANConfig("vector", 0, 500000)
        service.fn_connect(config)
        entered, release = Event(), Event()
        original = backend.fn_close

        def slow():
            entered.set()
            release.wait(3)
            original()

        backend.fn_close = slow
        thread = Thread(target=service.fn_disconnect)
        thread.start()
        try:
            self.assertTrue(entered.wait(2))
            self.assertEqual(service.snapshot.state, State.DISCONNECTING)
            with self.assertRaises(CANConnectionError):
                service.fn_connect(config)
            with self.assertRaises(CANConnectionError):
                service.fn_disconnect()
            with self.assertRaises(CANDiscoveryError):
                service.fn_refresh()
        finally:
            release.set()
            thread.join(3)
        self.assertEqual(backend.close_count, 1)

    def test_discovery_driver_close_failure_blocks_all_new_operations(self):
        from services.can import CANConnectionState as State, CANDiscoveryError
        from tests.services.test_vector_discovery import VectorDiscoveryTests
        backend, _, vector = VectorDiscoveryTests().backend()
        vector.xldriver.xlCloseDriver.side_effect = RuntimeError("cannot close driver")
        service = CANService(backend)
        with self.assertRaises(CANDiscoveryError):
            service.fn_refresh()
        self.assertEqual(service.snapshot.state, State.RECOVERY_REQUIRED)
        with self.assertRaises(CANConnectionError):
            service.fn_connect(CANConfig("vector", 0, 500000))

    def test_target_revalidation_refuses_reassigned_or_unplugged_global_index(self):
        snapshot = SimpleNamespace(channelCount=1, channel=[SimpleNamespace(
            channelIndex=8, serialNumber=222, hwType=57, hwIndex=1, hwChannel=1, channelBusCapabilities=65536)])
        can = Mock()
        backend = VectorBackend(can_module=can, vector_module=SimpleNamespace())
        with patch.object(backend, "_query_driver_config", return_value=(snapshot, 65536)):
            for config in (CANConfig("vector", 1, 500000, serial=111, channel_index=8),
                           CANConfig("vector", 1, 500000, serial=222, channel_index=9)):
                with self.assertRaises(CANConnectionError) as raised:
                    backend.fn_open(config)
                self.assertTrue(raised.exception.rediscovery_required)
            backend.fn_open(CANConfig("vector", 1, 500000, serial=222, channel_index=8, hw_type=57, hw_index=1, hw_channel=1))
        can.Bus.assert_called_once()

    def test_duplicate_connect_keeps_original_bus(self):
        can = Mock()
        backend = VectorBackend(can_module=can)
        config = CANConfig("vector", 0, 500000)
        backend.fn_open(config)
        bus = backend._bus
        with self.assertRaises(CANConnectionError):
            backend.fn_open(config)
        self.assertIs(backend._bus, bus)
        bus.shutdown.assert_not_called()
        can.Bus.assert_called_once()

    def test_failed_shutdown_retains_resource_and_blocks_reconnect(self):
        can = Mock()
        backend = VectorBackend(can_module=can)
        config = CANConfig("vector", 0, 500000)
        backend.fn_open(config)
        bus = backend._bus
        bus.shutdown.side_effect = RuntimeError("close failed")
        with self.assertRaises(CANConnectionError):
            backend.fn_close()
        self.assertIs(backend._bus, bus)
        with self.assertRaises(CANConnectionError):
            backend.fn_open(config)
        with self.assertRaises(CANConnectionError):
            backend.fn_close()
        bus.shutdown.assert_called_once()

    def test_service_tracks_active_config_and_clean_reconnect(self):
        from services.can import CANConnectionState
        service = CANService(FakeCANBackend())
        config = CANConfig("vector", 0, 500000)
        self.assertEqual(service.snapshot.state, CANConnectionState.DISCONNECTED)
        service.fn_connect(config)
        self.assertEqual(service.snapshot.state, CANConnectionState.CONNECTED)
        self.assertEqual(service.snapshot.config, config)
        with self.assertRaises(CANConnectionError):
            service.fn_connect(config)
        service.fn_disconnect()
        service.fn_disconnect()
        self.assertEqual(service.snapshot.state, CANConnectionState.DISCONNECTED)
        self.assertIsNone(service.snapshot.config)
        service.fn_connect(config)
        service.fn_disconnect()

    def test_service_rejects_overlap_without_blocking_state_reads(self):
        from services.can import CANConnectionState, CANDiscoveryError
        backend = FakeCANBackend()
        entered, release = Event(), Event()
        original = backend.fn_open

        def slow(config):
            entered.set()
            release.wait(3)
            original(config)

        backend.fn_open = slow
        service = CANService(backend)
        thread = Thread(target=service.fn_connect, args=(CANConfig("vector", 0, 500000),))
        thread.start()
        try:
            self.assertTrue(entered.wait(2))
            self.assertEqual(service.snapshot.state, CANConnectionState.CONNECTING)
            for operation in (service.fn_disconnect, lambda: service.fn_connect(CANConfig("vector", 1, 500000))):
                with self.assertRaises(CANConnectionError):
                    operation()
            with self.assertRaises(CANDiscoveryError):
                service.fn_refresh()
        finally:
            release.set()
            thread.join(3)
        service.fn_disconnect()

    def test_service_cleanup_failure_is_recovery_required(self):
        from services.can import CANConnectionState
        backend = FakeCANBackend()
        service = CANService(backend)
        config = CANConfig("vector", 0, 500000)
        service.fn_connect(config)
        backend.fn_close = Mock(side_effect=RuntimeError("driver close failed"))
        with self.assertRaises(CANConnectionError):
            service.fn_disconnect()
        self.assertEqual(service.snapshot.state, CANConnectionState.RECOVERY_REQUIRED)
        self.assertEqual(service.snapshot.config, config)
        self.assertFalse(service.fn_is_connected())
        with self.assertRaises(CANConnectionError):
            service.fn_connect(config)

