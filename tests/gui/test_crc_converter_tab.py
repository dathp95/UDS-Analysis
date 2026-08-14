import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QBuffer, QEvent, QIODevice, Qt
from PySide6.QtGui import QColor, QFocusEvent, QImage
from PySide6.QtWidgets import QApplication, QLabel, QHBoxLayout, QPlainTextEdit

from gui.tabs.crc_converter_tab import CRCConverterTab
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_combobox import PrimaryComboBox
from gui.widgets.controls.primary_lineedit import PrimaryLineEdit


def _png_bytes():
    image = QImage(16, 16, QImage.Format_RGB32)
    image.fill(QColor("white"))
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data())

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

    def test_transfer_crc_emits_normalized_crc_value(self):
        tab = CRCConverterTab()
        self.addCleanup(tab.deleteLater)
        emitted = []
        tab.crc_transfer_requested.connect(emitted.append)

        tab.txt_crc_output.setText("0x47")
        tab.btn_transfer_crc.click()

        self.assertEqual(emitted, ["47"])

    def test_transfer_crc_rejects_empty_output(self):
        tab = CRCConverterTab()
        self.addCleanup(tab.deleteLater)
        emitted = []
        tab.crc_transfer_requested.connect(emitted.append)

        with patch(
            "gui.tabs.crc_converter_tab.QMessageBox.warning"
        ) as warning:
            tab.btn_transfer_crc.click()

        warning.assert_called_once()
        self.assertEqual(emitted, [])
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
        self.assertFalse(tab.btn_converter_clear.isEnabled())
        self.assertFalse(tab.btn_converter_copy.isEnabled())

        panel_layout = tab.converter_panel.layout()
        editor_layout = panel_layout.itemAt(2).layout()
        action_layout = panel_layout.itemAt(3).layout()
        self.assertIsInstance(editor_layout, QHBoxLayout)
        self.assertIs(
            editor_layout.itemAt(0).layout().itemAt(1).widget(),
            tab.txt_converter_input,
        )
        self.assertIs(
            editor_layout.itemAt(1).layout().itemAt(1).widget(),
            tab.txt_converter_output,
        )
        left_action_layout = action_layout.itemAt(0).layout()
        right_action_layout = action_layout.itemAt(1).layout()
        self.assertIs(left_action_layout.itemAt(0).widget(), tab.btn_converter_convert)
        self.assertIs(left_action_layout.itemAt(1).widget(), tab.btn_converter_swap)
        self.assertIs(left_action_layout.itemAt(2).widget(), tab.btn_converter_clear)
        self.assertIs(right_action_layout.itemAt(0).widget(), tab.btn_converter_copy)
        self.assertEqual(action_layout.stretch(0), 1)
        self.assertEqual(action_layout.stretch(1), 1)

        self.assertIn("QR Code Generator", tab.lbl_qr_generator.text())
        self.assertIsInstance(tab.txt_qr_input, QPlainTextEdit)
        self.assertIsInstance(tab.lbl_qr_preview, QLabel)
        self.assertEqual(tab.lbl_qr_preview.alignment(), Qt.AlignCenter)
        self.assertEqual(tab.lbl_qr_preview.width(), 180)
        self.assertEqual(tab.lbl_qr_preview.height(), 180)
        self.assertEqual(tab.btn_create_qr.text(), "Create QR")
        self.assertEqual(tab.btn_copy_qr.text(), "Copy QR")
        self.assertEqual(tab.btn_clear_qr.text(), "Clear QR")
        self.assertFalse(tab.btn_copy_qr.isEnabled())
        self.assertFalse(tab.btn_clear_qr.isEnabled())
        self.assertIn(
            "QScrollBar:vertical",
            tab.txt_qr_input.verticalScrollBar().styleSheet(),
        )

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

    def test_create_qr_rejects_empty_input(self):
        tab = CRCConverterTab()
        self.addCleanup(tab.deleteLater)

        with patch(
            "gui.tabs.crc_converter_tab.QMessageBox.warning"
        ) as warning:
            tab.btn_create_qr.click()

        warning.assert_called_once()
        self.assertFalse(tab.btn_copy_qr.isEnabled())
        self.assertIsNone(tab._generated_qr_pixmap)

    def test_create_qr_displays_preview_and_copy_qr_copies_pixmap(self):
        tab = CRCConverterTab()
        self.addCleanup(tab.deleteLater)

        tab.txt_qr_input.setPlainText("hello qr")
        with patch(
            "gui.tabs.crc_converter_tab.generate_qr_png_bytes",
            return_value=_png_bytes(),
        ) as generate_qr:
            tab.btn_create_qr.click()

        generate_qr.assert_called_once_with("hello qr")
        self.assertTrue(tab.btn_copy_qr.isEnabled())
        self.assertIsNotNone(tab._generated_qr_pixmap)
        self.assertFalse(tab.lbl_qr_preview.pixmap().isNull())

        tab.btn_copy_qr.click()
        self.assertFalse(QApplication.clipboard().pixmap().isNull())

    def test_clear_qr_clears_input_preview_and_copy_state(self):
        tab = CRCConverterTab()
        self.addCleanup(tab.deleteLater)

        tab.txt_qr_input.setPlainText("hello qr")
        self.assertTrue(tab.btn_clear_qr.isEnabled())
        with patch(
            "gui.tabs.crc_converter_tab.generate_qr_png_bytes",
            return_value=_png_bytes(),
        ):
            tab.btn_create_qr.click()

        tab.btn_clear_qr.click()

        self.assertEqual(tab.txt_qr_input.toPlainText(), "")
        self.assertIsNone(tab._generated_qr_pixmap)
        self.assertTrue(tab.lbl_qr_preview.pixmap().isNull())
        self.assertFalse(tab.btn_copy_qr.isEnabled())
        self.assertFalse(tab.btn_clear_qr.isEnabled())


    def test_copy_qr_without_generated_image_shows_message(self):
        tab = CRCConverterTab()
        self.addCleanup(tab.deleteLater)

        with patch(
            "gui.tabs.crc_converter_tab.QMessageBox.information"
        ) as information:
            tab.copy_qr_code()

        information.assert_called_once()

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
        self.assertTrue(tab.btn_converter_clear.isEnabled())
        self.assertFalse(tab.btn_converter_copy.isEnabled())

        tab.btn_converter_convert.click()
        self.assertEqual(tab.txt_converter_output.toPlainText(), "65 66 67")
        self.assertTrue(tab.btn_converter_copy.isEnabled())

        tab.btn_converter_swap.click()
        self.assertEqual(tab.cmb_converter_from.currentText(), "Decimal")
        self.assertEqual(tab.cmb_converter_to.currentText(), "Hexadecimal")
        self.assertEqual(tab.txt_converter_input.toPlainText(), "65 66 67")
        self.assertEqual(tab.txt_converter_output.toPlainText(), "")
        self.assertFalse(tab.btn_converter_copy.isEnabled())

        tab.btn_converter_convert.click()
        self.assertEqual(tab.txt_converter_output.toPlainText(), "41 42 43")
        self.assertTrue(tab.btn_converter_copy.isEnabled())

        tab.btn_converter_copy.click()
        self.assertEqual(QApplication.clipboard().text(), "41 42 43")

        tab.btn_converter_clear.click()
        self.assertEqual(tab.cmb_converter_from.currentText(), "Hexadecimal")
        self.assertEqual(tab.cmb_converter_to.currentText(), "Decimal")
        self.assertEqual(tab.txt_converter_input.toPlainText(), "")
        self.assertEqual(tab.txt_converter_output.toPlainText(), "")
        self.assertFalse(tab.btn_converter_clear.isEnabled())
        self.assertFalse(tab.btn_converter_copy.isEnabled())
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
        self.assertTrue(tab.btn_converter_clear.isEnabled())
        self.assertFalse(tab.btn_converter_copy.isEnabled())

        tab.btn_converter_convert.click()
        self.assertEqual(tab.txt_converter_output.toPlainText(), "65 66 67")
        self.assertTrue(tab.btn_converter_copy.isEnabled())

        tab.txt_converter_input.setPlainText("41 GG")
        tab.btn_converter_convert.click()

        self.assertEqual(tab.txt_converter_output.toPlainText(), "")
        self.assertTrue(tab.btn_converter_clear.isEnabled())
        self.assertFalse(tab.btn_converter_copy.isEnabled())
        self.assertIn("Invalid HEX input", tab.txt_converter_input.toolTip())

if __name__ == "__main__":
    unittest.main()
