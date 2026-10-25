import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

from services.can import CANConfig, CANConnectionError, VectorBackend


class OwnedVectorBusTests(unittest.TestCase):
    def setUp(self):
        # Real installed VectorBus constructor, fake XL function boundary only.
        from can.interfaces.vector import canlib
        self.vector = canlib
        self.driver = Mock()
        self.driver.xlOpenPort.side_effect = lambda handle, *args: setattr(handle, "value", 7)
        self.patchers = [
            patch.object(canlib, "xldriver", self.driver),
            patch.object(canlib, "get_channel_configs", return_value=[SimpleNamespace(channel_index=5)]),
            patch.object(canlib.VectorBus, "_check_can_settings"),
        ]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.backend = VectorBackend(vector_module=canlib)
        self.config = CANConfig("vector", 5, 500000)

    def test_real_constructor_and_confirmed_shutdown_are_idempotent(self):
        self.backend.fn_open(self.config)
        self.assertTrue(self.backend.fn_is_connected())
        self.backend.fn_close()
        self.backend.fn_close()
        self.driver.xlClosePort.assert_called_once()
        self.driver.xlCloseDriver.assert_called_once()
        self.driver.xlCanTransmit.assert_not_called()
        self.driver.xlReceive.assert_not_called()

    def test_partial_initialization_releases_port_and_driver(self):
        self.driver.xlCanSetChannelMode.side_effect = RuntimeError("initialization failed")
        with self.assertRaises(CANConnectionError) as raised:
            self.backend.fn_open(self.config)
        self.assertFalse(raised.exception.recovery_required)
        self.assertFalse(self.backend.fn_is_connected())
        self.driver.xlClosePort.assert_called_once()
        self.driver.xlCloseDriver.assert_called_once()

    def test_driver_missing_is_not_partial_connected_bus(self):
        with patch.object(self.vector, "xldriver", None):
            with self.assertRaises(CANConnectionError) as raised:
                self.backend.fn_open(self.config)
        self.assertIn("Driver", str(raised.exception))
        self.assertFalse(raised.exception.recovery_required)
        self.assertIsNone(self.backend._bus)

    def test_open_port_failure_closes_only_acquired_driver(self):
        self.driver.xlOpenPort.side_effect = self.vector.VectorInitializationError(129, "hardware removed", "open")
        with self.assertRaises(CANConnectionError) as raised:
            self.backend.fn_open(self.config)
        self.assertTrue(raised.exception.rediscovery_required)
        self.assertFalse(raised.exception.recovery_required)
        self.driver.xlClosePort.assert_not_called()
        self.driver.xlCloseDriver.assert_called_once()

    def test_activation_failure_cleans_without_double_close(self):
        self.driver.xlActivateChannel.side_effect = self.vector.VectorOperationError(129, "hardware removed", "activate")
        with self.assertRaises(CANConnectionError) as raised:
            self.backend.fn_open(self.config)
        self.assertFalse(raised.exception.recovery_required)
        self.driver.xlClosePort.assert_called_once()
        self.driver.xlCloseDriver.assert_called_once()

    def test_close_driver_failure_retains_owner_and_prevents_reopen(self):
        self.backend.fn_open(self.config)
        self.driver.xlCloseDriver.side_effect = self.vector.VectorOperationError(201, "driver failed", "close")
        with self.assertRaises(CANConnectionError):
            self.backend.fn_close()
        self.assertTrue(self.backend.recovery_required)
        self.assertIsNotNone(self.backend._bus)
        with self.assertRaises(CANConnectionError):
            self.backend.fn_open(self.config)
        self.driver.xlClosePort.assert_called_once()
        self.driver.xlCloseDriver.assert_called_once()

    def test_partial_cleanup_failure_retains_bus_without_retry(self):
        self.driver.xlCanSetChannelMode.side_effect = RuntimeError("initialization failed")
        self.driver.xlClosePort.side_effect = RuntimeError("close failed")
        with self.assertRaises(CANConnectionError) as raised:
            self.backend.fn_open(self.config)
        self.assertTrue(raised.exception.recovery_required)
        self.assertIsNotNone(self.backend._bus)
        with self.assertRaises(CANConnectionError):
            self.backend.fn_close()
        self.driver.xlClosePort.assert_called_once()
        self.driver.xlCloseDriver.assert_not_called()

    def test_deactivate_failure_does_not_skip_port_close(self):
        self.backend.fn_open(self.config)
        self.driver.xlDeactivateChannel.side_effect = self.vector.VectorOperationError(129, "hardware lost", "deactivate")
        self.backend.fn_close()
        self.assertIsNone(self.backend._bus)
        self.driver.xlClosePort.assert_called_once()
        self.driver.xlCloseDriver.assert_called_once()

    def test_suppressed_upstream_close_error_is_reported(self):
        self.backend.fn_open(self.config)
        self.driver.xlClosePort.side_effect = self.vector.VectorOperationError(118, "invalid port", "close")
        with self.assertRaises(CANConnectionError) as raised:
            self.backend.fn_close()
        self.assertTrue(raised.exception.recovery_required)
        self.assertIsNotNone(self.backend._bus)

