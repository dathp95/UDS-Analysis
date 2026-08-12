import unittest

from core.crc import calculate_crc8_sae_j1850, parse_hex_bytes


class CRCTests(unittest.TestCase):

    def test_parse_hex_bytes_accepts_spaces_newlines_and_case(self):
        self.assertEqual(
            parse_hex_bytes("01 02\n0a FF"),
            bytes([0x01, 0x02, 0x0A, 0xFF]),
        )

    def test_parse_hex_bytes_accepts_contiguous_hex(self):
        self.assertEqual(
            parse_hex_bytes("0102030405"),
            bytes([0x01, 0x02, 0x03, 0x04, 0x05]),
        )

    def test_parse_hex_bytes_rejects_invalid_or_odd_length_hex(self):
        invalid_values = [
            "01 ZZ",
            "01 2",
            "010",
        ]

        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_hex_bytes(value)

    def test_calculate_crc8_sae_j1850(self):
        data = parse_hex_bytes("01 02 03 04 05")

        self.assertEqual(calculate_crc8_sae_j1850(data), 0x95)

    def test_empty_payload_crc_is_zero(self):
        self.assertEqual(calculate_crc8_sae_j1850(b""), 0x00)


if __name__ == "__main__":
    unittest.main()
