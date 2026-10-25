import unittest

from services.can import CANChannelInfo, CANDeviceInfo, CANDiscoveryError, CANConfig, CANService, CANValidationError


class FakeCANBackend:

    def __init__(self):
        self.opened_config = None
        self.close_count = 0
        self.connected = False
        self.refresh_count = 0
        self.devices = ()

    def fn_open(self, config):
        self.opened_config = config
        self.connected = True

    def fn_close(self):
        self.close_count += 1
        self.connected = False

    def fn_is_connected(self):
        return self.connected

    def fn_refresh(self):
        self.refresh_count += 1
        return self.devices


class CANServiceTests(unittest.TestCase):

    def test_connect_validates_and_opens_backend(self):
        backend = FakeCANBackend()
        service = CANService(backend=backend)
        config = CANConfig(
            interface="vector",
            channel=1,
            bitrate=500000,
        )

        service.fn_connect(config)

        self.assertEqual(backend.opened_config, config)
        self.assertTrue(service.fn_is_connected())

    def test_disconnect_releases_backend(self):
        backend = FakeCANBackend()
        service = CANService(backend=backend)

        service.fn_connect(CANConfig("vector", 0, 500000))
        service.fn_disconnect()

        self.assertEqual(backend.close_count, 1)
        self.assertFalse(service.fn_is_connected())

    def test_rejects_invalid_channel_without_opening_backend(self):
        backend = FakeCANBackend()
        service = CANService(backend=backend)

        with self.assertRaises(CANValidationError):
            service.fn_connect(CANConfig("vector", -1, 500000))

        self.assertIsNone(backend.opened_config)

    def test_rejects_unsupported_bitrate_without_opening_backend(self):
        backend = FakeCANBackend()
        service = CANService(backend=backend)

        with self.assertRaises(CANValidationError):
            service.fn_connect(CANConfig("vector", 0, 333000))

        self.assertIsNone(backend.opened_config)

    def test_rejects_unsupported_interface_without_opening_backend(self):
        backend = FakeCANBackend()
        service = CANService(backend=backend)

        with self.assertRaises(CANValidationError):
            service.fn_connect(CANConfig("socketcan", 0, 500000))

        self.assertIsNone(backend.opened_config)

    def test_refresh_delegates_to_backend(self):
        backend = FakeCANBackend()
        service = CANService(backend=backend)

        service.fn_refresh()

        self.assertEqual(backend.refresh_count, 1)

    def test_refresh_returns_immutable_devices_and_preserves_empty_result(self):
        backend = FakeCANBackend()
        service = CANService(backend)
        self.assertEqual(service.fn_refresh(), ())
        device = CANDeviceInfo("Vector Device", 100, 57, 0, (CANChannelInfo(0, 7, "CAN 1", False),))
        backend.devices = [device]
        self.assertEqual(service.fn_refresh(), (device,))

    def test_refresh_rejects_invalid_or_ambiguous_metadata(self):
        backend = FakeCANBackend()
        service = CANService(backend)
        first = CANDeviceInfo("Vector", 100, 57, 0, (CANChannelInfo(0, 7, "CAN 1", False),))
        second = CANDeviceInfo("Vector", 200, 57, 1, (CANChannelInfo(0, 7, "CAN 1", False),))
        for devices in (None, ({},), (first, second)):
            backend.devices = devices
            with self.assertRaises(CANDiscoveryError):
                service.fn_refresh()

    def test_refresh_while_connected_never_queries_or_closes_backend(self):
        backend = FakeCANBackend()
        service = CANService(backend)
        service.fn_connect(CANConfig("vector", 0, 500000))
        with self.assertRaises(CANDiscoveryError):
            service.fn_refresh()
        self.assertEqual(backend.refresh_count, 0)
        self.assertEqual(backend.close_count, 0)
        self.assertTrue(service.fn_is_connected())

    def test_optional_metadata_validation_does_not_break_legacy_constructor(self):
        backend = FakeCANBackend()
        service = CANService(backend)
        service.fn_connect(CANConfig("vector", 0, 500000))
        self.assertIsNone(backend.opened_config.serial)
        self.assertIsNone(backend.opened_config.channel_index)
        with self.assertRaises(CANValidationError):
            service.fn_connect(CANConfig("vector", 0, 500000, channel_index=-1))


if __name__ == "__main__":
    unittest.main()
