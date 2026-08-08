import unittest

from gui.utils.payload_format import delete_payload_character_at_cursor
from gui.utils.payload_format import format_payload_input
from gui.utils.payload_format import format_payload_input_with_cursor


class PayloadFormatTests(unittest.TestCase):
    def test_compact_payload_is_grouped(self):
        self.assertEqual(format_payload_input("22f190"), "22 F1 90")

    def test_existing_spacing_is_normalized(self):
        self.assertEqual(format_payload_input("22  f1  90"), "22 F1 90")

    def test_free_form_filter_text_is_preserved(self):
        self.assertEqual(format_payload_input("VIN"), "VIN")

    def test_format_payload_preserves_logical_cursor_position(self):
        formatted, cursor = format_payload_input_with_cursor(
            "22 F31 90",
            5,
        )

        self.assertEqual(formatted, "22 F3 19 0")
        self.assertEqual(cursor, 5)

    def test_delete_payload_character_skips_spacing_after_cursor(self):
        formatted, cursor = delete_payload_character_at_cursor(
            "22 F3 19 0",
            5,
        )

        self.assertEqual(formatted, "22 F3 90")
        self.assertEqual(cursor, 5)


if __name__ == "__main__":
    unittest.main()
