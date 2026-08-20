import unittest

from services.can import CANConfig, CANService, CANValidationError


class FakeCANBackend:

    def __init__(self):
        self.opened_config = None
        self.close_count = 0
        self.connected = False
        self.refresh_count = 0

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
        return None


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


if __name__ == "__main__":
    unittest.main()
