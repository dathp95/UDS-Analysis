import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QHBoxLayout, QPlainTextEdit

from gui.tabs.crc_converter_tab import CRCConverterTab
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_lineedit import PrimaryLineEdit


class CRCConverterTabTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_crc_converter_panel_has_expected_controls(self):
        tab = CRCConverterTab()
        self.addCleanup(tab.deleteLater)

        self.assertEqual(tab.lbl_crc8_sae_j1850.text(), "CRC8_SAE_J1850")
        self.assertIsInstance(tab.txt_crc_input, QPlainTextEdit)
        self.assertEqual(tab.txt_crc_input.placeholderText(), "01 02 03 04 05")
        self.assertEqual(
            tab.txt_crc_input.verticalScrollBarPolicy(),
            Qt.ScrollBarAsNeeded,
        )
        self.assertIn(
            "QScrollBar:vertical",
            tab.txt_crc_input.verticalScrollBar().styleSheet(),
        )
        self.assertEqual(
            tab.txt_crc_input.minimumHeight(),
            tab.txt_crc_input.maximumHeight(),
        )
        self.assertIsInstance(tab.btn_calculate_crc, PrimaryButton)
        self.assertEqual(tab.btn_calculate_crc.text(), "Calculate CRC")
        self.assertIsInstance(tab.txt_crc_output, PrimaryLineEdit)
        self.assertTrue(tab.txt_crc_output.isReadOnly())

    def test_tab_layout_is_split_between_crc_and_converter(self):
        tab = CRCConverterTab()
        self.addCleanup(tab.deleteLater)

        main_layout = tab.layout()

        self.assertIsInstance(main_layout, QHBoxLayout)
        self.assertEqual(main_layout.count(), 2)
        self.assertIs(main_layout.itemAt(0).widget(), tab.crc_panel)
        self.assertIs(main_layout.itemAt(1).widget(), tab.converter_panel)
        self.assertEqual(main_layout.stretch(0), 1)
        self.assertEqual(main_layout.stretch(1), 1)
        self.assertEqual(tab.lbl_converter.text(), "Converter")

    def test_calculate_crc_button_renders_hex_result(self):
        tab = CRCConverterTab()
        self.addCleanup(tab.deleteLater)

        tab.txt_crc_input.setPlainText("01 02\n03 04 05")
        tab.btn_calculate_crc.click()

        self.assertEqual(tab.txt_crc_output.text(), "95")

    def test_invalid_input_does_not_crash_or_keep_stale_result(self):
        tab = CRCConverterTab()
        self.addCleanup(tab.deleteLater)

        tab.txt_crc_input.setPlainText("01 02 03 04 05")
        tab.btn_calculate_crc.click()
        self.assertEqual(tab.txt_crc_output.text(), "95")

        tab.txt_crc_input.setPlainText("01 ZZ")
        tab.btn_calculate_crc.click()

        self.assertEqual(tab.txt_crc_output.text(), "")
        self.assertIn("Invalid HEX input", tab.txt_crc_input.toolTip())


if __name__ == "__main__":
    unittest.main()
