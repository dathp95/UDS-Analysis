import unittest

from gui.utils.payload_format import format_payload_input


class PayloadFormatTests(unittest.TestCase):
    def test_compact_payload_is_grouped(self):
        self.assertEqual(format_payload_input("22f190"), "22 F1 90")

    def test_existing_spacing_is_normalized(self):
        self.assertEqual(format_payload_input("22  f1  90"), "22 F1 90")

    def test_free_form_filter_text_is_preserved(self):
        self.assertEqual(format_payload_input("VIN"), "VIN")


if __name__ == "__main__":
    unittest.main()
