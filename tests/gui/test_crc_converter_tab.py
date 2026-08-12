import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QFocusEvent
from PySide6.QtWidgets import QApplication, QHBoxLayout, QPlainTextEdit

from gui.tabs.crc_converter_tab import CRCConverterTab
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_combobox import PrimaryComboBox
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

    def test_converter_panel_has_expected_controls_and_defaults(self):
        tab = CRCConverterTab()
        self.addCleanup(tab.deleteLater)

        self.assertEqual(tab.lbl_converter.text(), "Converter")
        self.assertEqual(tab.lbl_converter_from.text(), "From")
        self.assertEqual(tab.lbl_converter_to.text(), "To")
        self.assertIsInstance(tab.cmb_converter_from, PrimaryComboBox)
        self.assertIsInstance(tab.cmb_converter_to, PrimaryComboBox)
        self.assertEqual(tab.cmb_converter_from.currentText(), "Hexadecimal")
        self.assertEqual(tab.cmb_converter_to.currentText(), "Decimal")
        self.assertEqual(
            [
                tab.cmb_converter_from.itemText(index)
                for index in range(tab.cmb_converter_from.count())
            ],
            ["Hexadecimal", "Decimal", "ASCII", "Binary", "TXT", "Octa"],
        )
        self.assertIsInstance(tab.txt_converter_input, QPlainTextEdit)
        self.assertIsInstance(tab.txt_converter_output, QPlainTextEdit)
        self.assertTrue(tab.txt_converter_output.isReadOnly())
        self.assertIn(
            "QScrollBar:vertical",
            tab.txt_converter_input.verticalScrollBar().styleSheet(),
        )
        self.assertIn(
            "QScrollBar:vertical",
            tab.txt_converter_output.verticalScrollBar().styleSheet(),
        )
        self.assertEqual(tab.btn_converter_convert.text(), "CONVERT")
        self.assertEqual(tab.btn_converter_swap.text(), "SWAP")
        self.assertEqual(tab.btn_converter_clear.text(), "CLEAR")
        self.assertEqual(tab.btn_converter_copy.text(), "Copy Result")

    def test_text_selection_is_cleared_when_crc_editor_loses_focus(self):
        tab = CRCConverterTab()
        self.addCleanup(tab.deleteLater)

        tab.txt_crc_input.setPlainText("01 02 03")
        tab.txt_crc_input.selectAll()
        self.assertNotEqual(tab.txt_crc_input.textCursor().selectedText(), "")

        QApplication.sendEvent(
            tab.txt_crc_input,
            QFocusEvent(QEvent.FocusOut),
        )

        self.assertEqual(tab.txt_crc_input.textCursor().selectedText(), "")

    def test_text_selection_is_cleared_when_crc_lineedit_loses_focus(self):
        tab = CRCConverterTab()
        self.addCleanup(tab.deleteLater)

        tab.txt_crc_output.setText("95")
        tab.txt_crc_output.selectAll()
        self.assertEqual(tab.txt_crc_output.selectedText(), "95")

        QApplication.sendEvent(
            tab.txt_crc_output,
            QFocusEvent(QEvent.FocusOut),
        )

        self.assertEqual(tab.txt_crc_output.selectedText(), "")
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

    def test_converter_convert_swap_clear_and_copy(self):
        tab = CRCConverterTab()
        self.addCleanup(tab.deleteLater)

        tab.txt_converter_input.setPlainText("41 42 43")
        tab.btn_converter_convert.click()
        self.assertEqual(tab.txt_converter_output.toPlainText(), "65 66 67")

        tab.btn_converter_swap.click()
        self.assertEqual(tab.cmb_converter_from.currentText(), "Decimal")
        self.assertEqual(tab.cmb_converter_to.currentText(), "Hexadecimal")
        self.assertEqual(tab.txt_converter_input.toPlainText(), "65 66 67")
        self.assertEqual(tab.txt_converter_output.toPlainText(), "")

        tab.btn_converter_convert.click()
        self.assertEqual(tab.txt_converter_output.toPlainText(), "41 42 43")

        tab.btn_converter_copy.click()
        self.assertEqual(QApplication.clipboard().text(), "41 42 43")

        tab.btn_converter_clear.click()
        self.assertEqual(tab.cmb_converter_from.currentText(), "Hexadecimal")
        self.assertEqual(tab.cmb_converter_to.currentText(), "Decimal")
        self.assertEqual(tab.txt_converter_input.toPlainText(), "")
        self.assertEqual(tab.txt_converter_output.toPlainText(), "")

    def test_converter_supports_new_formats_from_the_ui(self):
        tab = CRCConverterTab()
        self.addCleanup(tab.deleteLater)

        tab._set_combo_text(tab.cmb_converter_from, "TXT")
        tab._set_combo_text(tab.cmb_converter_to, "Binary")
        tab.txt_converter_input.setPlainText("ABC")
        tab.btn_converter_convert.click()

        self.assertEqual(
            tab.txt_converter_output.toPlainText(),
            "01000001 01000010 01000011",
        )

        tab._set_combo_text(tab.cmb_converter_from, "Octa")
        tab._set_combo_text(tab.cmb_converter_to, "TXT")
        tab.txt_converter_input.setPlainText("101 102 103")
        tab.btn_converter_convert.click()

        self.assertEqual(tab.txt_converter_output.toPlainText(), "ABC")

    def test_converter_invalid_input_does_not_crash_or_keep_stale_result(self):
        tab = CRCConverterTab()
        self.addCleanup(tab.deleteLater)

        tab.txt_converter_input.setPlainText("41 42 43")
        tab.btn_converter_convert.click()
        self.assertEqual(tab.txt_converter_output.toPlainText(), "65 66 67")

        tab.txt_converter_input.setPlainText("41 GG")
        tab.btn_converter_convert.click()

        self.assertEqual(tab.txt_converter_output.toPlainText(), "")
        self.assertIn("Invalid HEX input", tab.txt_converter_input.toolTip())


if __name__ == "__main__":
    unittest.main()
