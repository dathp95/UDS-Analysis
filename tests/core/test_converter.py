import unittest

from core.converter import convert_data


class ConverterTests(unittest.TestCase):

    def test_hex_to_decimal_and_ascii(self):
        self.assertEqual(
            convert_data("41 42 43", "Hexadecimal", "Decimal"),
            "65 66 67",
        )
        self.assertEqual(
            convert_data("41 42 43", "Hexadecimal", "ASCII"),
            "ABC",
        )

    def test_hex_accepts_contiguous_and_prefixed_tokens(self):
        self.assertEqual(
            convert_data("414243", "Hexadecimal", "Decimal"),
            "65 66 67",
        )
        self.assertEqual(
            convert_data("0x41 0x42 0x43", "Hexadecimal", "ASCII"),
            "ABC",
        )

    def test_decimal_to_hex_and_ascii(self):
        self.assertEqual(
            convert_data("65 66 67", "Decimal", "Hexadecimal"),
            "41 42 43",
        )
        self.assertEqual(
            convert_data("65 66 67", "Decimal", "ASCII"),
            "ABC",
        )

    def test_ascii_to_hex_and_decimal(self):
        self.assertEqual(
            convert_data("ABC", "ASCII", "Hexadecimal"),
            "41 42 43",
        )
        self.assertEqual(
            convert_data("ABC", "ASCII", "Decimal"),
            "65 66 67",
        )

    def test_binary_conversions_are_byte_based(self):
        self.assertEqual(
            convert_data("01000001 01000010 01000011", "Binary", "TXT"),
            "ABC",
        )
        self.assertEqual(
            convert_data("010000010100001001000011", "Binary", "Hexadecimal"),
            "41 42 43",
        )
        self.assertEqual(
            convert_data("ABC", "TXT", "Binary"),
            "01000001 01000010 01000011",
        )

    def test_txt_uses_utf8(self):
        self.assertEqual(
            convert_data("ABC", "TXT", "Hexadecimal"),
            "41 42 43",
        )
        self.assertEqual(
            convert_data("C3 A9", "Hexadecimal", "TXT"),
            "é",
        )
        self.assertEqual(
            convert_data("é", "TXT", "Hexadecimal"),
            "C3 A9",
        )

    def test_octa_conversions_are_byte_based(self):
        self.assertEqual(
            convert_data("101 102 103", "Octa", "TXT"),
            "ABC",
        )
        self.assertEqual(
            convert_data("ABC", "TXT", "Octa"),
            "101 102 103",
        )
        self.assertEqual(
            convert_data("377", "Octa", "Decimal"),
            "255",
        )

    def test_rejects_invalid_input(self):
        invalid_cases = [
            ("414", "Hexadecimal", "Decimal"),
            ("41 GG", "Hexadecimal", "Decimal"),
            ("65 nope", "Decimal", "Hexadecimal"),
            ("256", "Decimal", "Hexadecimal"),
            ("ABC", "ASCII", "ASCII"),
            ("0100000", "Binary", "Decimal"),
            ("0100000Z", "Binary", "Decimal"),
            ("400", "Octa", "Decimal"),
            ("9", "Octa", "Decimal"),
            ("FF", "Hexadecimal", "ASCII"),
            ("FF", "Hexadecimal", "TXT"),
        ]

        for value, source, target in invalid_cases:
            with self.subTest(value=value, source=source, target=target):
                with self.assertRaises(ValueError):
                    convert_data(value, source, target)


if __name__ == "__main__":
    unittest.main()
