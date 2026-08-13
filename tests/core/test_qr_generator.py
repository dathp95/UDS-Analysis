import sys
import types
import unittest
from unittest.mock import patch

from core.qr_generator import QRDependencyError, generate_qr_png_bytes


class QRGeneratorTests(unittest.TestCase):

    def test_rejects_empty_input(self):
        with self.assertRaises(ValueError):
            generate_qr_png_bytes("   ")

    def test_generates_png_bytes_without_writing_files(self):
        class FakeImage:
            def save(self, buffer, format):
                self.format = format
                buffer.write(b"PNGDATA")

        class FakeQRCode:
            def __init__(self, error_correction, box_size, border):
                self.error_correction = error_correction
                self.box_size = box_size
                self.border = border
                self.data = None
                self.fit = None

            def add_data(self, data):
                self.data = data

            def make(self, fit):
                self.fit = fit

            def make_image(self, fill_color, back_color):
                self.fill_color = fill_color
                self.back_color = back_color
                return FakeImage()

        fake_qrcode = types.SimpleNamespace(
            QRCode=FakeQRCode,
            constants=types.SimpleNamespace(ERROR_CORRECT_M=0),
        )

        with patch.dict(sys.modules, {"qrcode": fake_qrcode}):
            self.assertEqual(
                generate_qr_png_bytes("hello"),
                b"PNGDATA",
            )

    def test_reports_missing_dependency(self):
        with patch.dict(sys.modules, {"qrcode": None}):
            with self.assertRaises(QRDependencyError):
                generate_qr_png_bytes("hello")


if __name__ == "__main__":
    unittest.main()