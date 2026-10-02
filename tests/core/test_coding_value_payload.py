import unittest

from core.coding_value_payload import (
    extract_raw_value,
    format_payload_bytes,
    normalize_user_raw_value,
    parse_payload_text,
    write_raw_value,
)


class CodingValuePayloadTests(unittest.TestCase):

    def test_parse_payload_text_accepts_lowercase_and_whitespace(self):
        self.assertEqual(
            parse_payload_text("62 f1\n90 0a xx 7"),
            [0x62, 0xF1, 0x90, 0x0A],
        )

    def test_format_payload_bytes_uses_uppercase_pairs(self):
        self.assertEqual(
            format_payload_bytes([0x00, 0x0A, 0xF1]),
            "00 0A F1",
        )

    def test_extract_and_write_full_byte(self):
        payload = [0xAA, 0x12, 0xBB]

        self.assertEqual(extract_raw_value(payload, 1, 0, 8), "12")
        result = write_raw_value(payload, 1, 0, 8, "34")

        self.assertTrue(result.success)
        self.assertEqual(result.changed_indexes, [1])
        self.assertEqual(result.payload, [0xAA, 0x34, 0xBB])
        self.assertEqual(payload, [0xAA, 0x12, 0xBB])

    def test_extract_and_write_low_nibble_preserves_high_nibble(self):
        payload = [0xA5]

        self.assertEqual(extract_raw_value(payload, 0, 0, 4), "05")
        result = write_raw_value(payload, 0, 0, 4, "0B")

        self.assertEqual(result.payload, [0xAB])
        self.assertEqual(result.changed_indexes, [0])

    def test_extract_and_write_high_nibble_preserves_low_nibble(self):
        payload = [0xA5]

        self.assertEqual(extract_raw_value(payload, 0, 4, 4), "0A")
        result = write_raw_value(payload, 0, 4, 4, "03")

        self.assertEqual(result.payload, [0x35])
        self.assertEqual(result.changed_indexes, [0])

    def test_extract_and_write_multi_byte_in_payload_order(self):
        payload = [0xAA, 0x12, 0x34, 0xBB]

        self.assertEqual(extract_raw_value(payload, 1, 0, 16), "12 34")
        result = write_raw_value(payload, 1, 0, 16, "56 78")

        self.assertEqual(result.payload, [0xAA, 0x56, 0x78, 0xBB])
        self.assertEqual(result.changed_indexes, [1, 2])

    def test_write_cross_byte_bit_field_preserves_unrelated_bits(self):
        payload = [0xF0, 0x0F]

        self.assertEqual(extract_raw_value(payload, 0, 4, 8), "FF")
        result = write_raw_value(payload, 0, 4, 8, "00")

        self.assertEqual(result.payload, [0x00, 0x00])
        self.assertEqual(result.changed_indexes, [0, 1])

    def test_invalid_extract_and_write_return_empty_or_unchanged(self):
        payload = [0x12]

        self.assertEqual(extract_raw_value(payload, 2, 0, 8), "")
        self.assertEqual(extract_raw_value(payload, 0, 0, 16), "")
        result = write_raw_value(payload, 2, 0, 8, "34")

        self.assertFalse(result.success)
        self.assertEqual(result.payload, payload)
        self.assertEqual(result.changed_indexes, [])

    def test_raw_value_too_large_for_full_byte_write_is_unchanged(self):
        payload = [0x12]

        result = write_raw_value(payload, 0, "0", "8.0", "1FF")

        self.assertFalse(result.success)
        self.assertEqual(result.payload, payload)
        self.assertEqual(result.changed_indexes, [])

    def test_normalize_user_raw_value_keeps_existing_nibble_semantics(self):
        self.assertEqual(normalize_user_raw_value("8 9", "4 bit"), "08 09")
        self.assertIsNone(normalize_user_raw_value("10 09", "4 bit"))


if __name__ == "__main__":
    unittest.main()
