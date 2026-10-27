import unittest

from services.seed_key_provider import (
    MockSeedKeyProvider,
)

from services.can.security_seed_parser import (
    parse_security_seed,
    SecuritySeedError,
)

from services.can.security_key_service import (
    SecurityKeyService,
)


class TestSecurityKeyService(unittest.TestCase):

    def setUp(self):
        self.service = SecurityKeyService(
            MockSeedKeyProvider()
        )

    def test_parse_seed(self):
        result = parse_security_seed(
            bytes.fromhex("27 01"),
            bytes.fromhex(
                "67 01 12 34 56 78"
            ),
        )

        self.assertEqual(
            result.seed,
            bytes.fromhex("12 34 56 78"),
        )

    def test_seed_missing(self):
        with self.assertRaises(
            SecuritySeedError
        ):
            parse_security_seed(
                bytes.fromhex("27 01"),
                bytes.fromhex("67 01"),
            )

    def test_negative_response(self):
        with self.assertRaises(
            SecuritySeedError
        ):
            parse_security_seed(
                bytes.fromhex("27 01"),
                bytes.fromhex("7F 27 33"),
            )

    def test_reject_other_level(self):
        with self.assertRaises(
            SecuritySeedError
        ):
            parse_security_seed(
                bytes.fromhex("27 03"),
                bytes.fromhex(
                    "67 03 12 34 56 78"
                ),
            )

    def test_mock_key_calculation(self):
        result = self.service.calculate_from_response(
            vehicle="TEST_VEHICLE",
            ecu="TEST_ECU",
            request_payload=bytes.fromhex(
                "27 01"
            ),
            response_payload=bytes.fromhex(
                "67 01 12 34 56 78"
            ),
            output_size=16,
        )

        self.assertEqual(
            len(result.key),
            16,
        )

        self.assertTrue(
            result.mock_only
        )


if __name__ == "__main__":
    unittest.main()