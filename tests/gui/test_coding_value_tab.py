import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from openpyxl import Workbook, load_workbook

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QHBoxLayout, QHeaderView, QPlainTextEdit, QVBoxLayout

from config.paths import CONFIG_DIR, EXPORT_CODING_FILES_DIR
from gui.themes.theme_manager import ThemeManager
from gui.widgets.coding_value.coding_value_panel import CodingValuePanel
from gui.widgets.coding_value.coding_value_table import CodingValueTable


class CodingValueTabTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.export_dir_handle = tempfile.TemporaryDirectory()
        self.addCleanup(self.export_dir_handle.cleanup)
        self.export_dir_patch = patch(
            "gui.widgets.coding_value.coding_value_panel.EXPORT_CODING_FILES_DIR",
            Path(self.export_dir_handle.name) / "config" / "export_coding_files",
        )
        self.export_dir_patch.start()
        self.addCleanup(self.export_dir_patch.stop)

    def test_export_coding_files_dir_lives_under_config(self):
        self.assertEqual(
            EXPORT_CODING_FILES_DIR,
            CONFIG_DIR / "export_coding_files",
        )

    def test_file_path_starts_empty(self):
        panel = CodingValuePanel()
        self.addCleanup(panel.deleteLater)

        self.assertEqual(panel.file_path.text(), "")

    def test_json_drop_list_starts_empty_between_browse_and_import(self):
        panel = CodingValuePanel()
        self.addCleanup(panel.deleteLater)

        file_layout = panel.file_row.layout()
        self.assertEqual(file_layout.indexOf(panel.btn_browse), 1)
        self.assertEqual(file_layout.indexOf(panel.cmb_coding_json), 2)
        self.assertEqual(file_layout.indexOf(panel.btn_import), 3)
        self.assertEqual(panel.cmb_coding_json.width(), 200)
        self.assertEqual(panel.cmb_coding_json.maxVisibleItems(), 5)
        self.assertIn(
            "QScrollBar:vertical",
            panel.cmb_coding_json.view().verticalScrollBar().styleSheet(),
        )
        self.assertEqual(panel.cmb_coding_json.currentText(), "")

    def test_import_coding_excel_renders_table_with_decoded_combobox(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "DID Number (hex)",
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "0xF112",
            "Vehicle Name",
            3,
            0,
            8,
            "0x1=VF3\n0xFF=Invalid",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.txt_coding_value.setPlainText("62 F1 12 FF")
            panel.import_coding_value()

        self.assertEqual(panel.table.rowCount(), 1)
        self.assertEqual(panel.table.item(0, 0).text(), "Vehicle Name")
        self.assertEqual(panel.table.item(0, 4).text(), "")

        combo = panel.table.cellWidget(0, 5)
        self.assertEqual(combo.currentText(), "")
        self.assertEqual(combo.count(), 2)

        panel.encode_coding_payload()
        self.assertEqual(panel.table.item(0, 4).text(), "FF")
        self.assertEqual(combo.currentText(), "Invalid")

        combo.setCurrentIndex(combo.findText("VF3"))
        self.assertEqual(panel.table.item(0, 4).text(), "01")

        panel.table.item(0, 4).setText("FF")
        self.assertEqual(combo.currentText(), "Invalid")
        panel.table.item(0, 4).setText("01")
        self.assertEqual(combo.currentText(), "VF3")

    def test_import_coding_excel_exports_parsed_rows_to_json(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Vehicle Name",
            13,
            0,
            8,
            "0x03=VF3\n0x09=VF7NP",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            export_dir = Path(tmpdir) / "config" / "export_coding_files"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))

            with patch(
                "gui.widgets.coding_value.coding_value_panel.EXPORT_CODING_FILES_DIR",
                export_dir,
            ):
                panel.import_coding_value()

            exported_path = export_dir / "coding.json"
            self.assertTrue(exported_path.exists())
            exported = json.loads(exported_path.read_text(encoding="utf-8"))

        self.assertEqual(exported["source_file"], "coding.xlsx")
        self.assertEqual(exported["rows"][0]["parameter"], "Vehicle Name")
        self.assertEqual(exported["rows"][0]["byte_pos"], "13")
        self.assertEqual(exported["rows"][0]["bit_pos"], "0")
        self.assertEqual(exported["rows"][0]["bit_length"], "8")
        self.assertEqual(
            exported["rows"][0]["decoded_options"],
            [
                {"raw_value": "0x03", "label": "VF3"},
                {"raw_value": "0x09", "label": "VF7NP"},
            ],
        )
    def test_selecting_json_drop_list_loads_table_from_export_folder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_dir = Path(tmpdir) / "config" / "export_coding_files"
            export_dir.mkdir(parents=True)
            json_path = export_dir / "existing.json"
            json_path.write_text(
                json.dumps({
                    "source_file": "existing.xlsx",
                    "rows": [
                        {
                            "parameter": "Method Type",
                            "byte_pos": "14",
                            "bit_pos": "0",
                            "bit_length": "8",
                            "raw_value": "",
                            "decoded_value": "",
                            "decoded_options": [
                                {"raw_value": "0x05", "label": "Sky"},
                            ],
                        },
                    ],
                }),
                encoding="utf-8",
            )

            with patch(
                "gui.widgets.coding_value.coding_value_panel.EXPORT_CODING_FILES_DIR",
                export_dir,
            ):
                panel = CodingValuePanel()
                self.addCleanup(panel.deleteLater)
                panel.cmb_coding_json.setCurrentIndex(
                    panel.cmb_coding_json.findText("existing")
                )

        self.assertEqual(panel.table.rowCount(), 1)
        self.assertEqual(panel.table.item(0, 0).text(), "Method Type")
        self.assertEqual(panel.table.item(0, 4).text(), "")
        self.assertEqual(panel.table.cellWidget(0, 5).currentText(), "")
    def test_import_button_loads_selected_json_without_excel_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            export_dir = Path(tmpdir) / "config" / "export_coding_files"
            export_dir.mkdir(parents=True)
            json_path = export_dir / "existing.json"
            json_path.write_text(
                json.dumps({
                    "source_file": "existing.xlsx",
                    "rows": [
                        {
                            "parameter": "Method Type",
                            "byte_pos": "14",
                            "bit_pos": "0",
                            "bit_length": "8",
                            "raw_value": "",
                            "decoded_value": "",
                            "decoded_options": [
                                {"raw_value": "0x05", "label": "Sky"},
                            ],
                        },
                    ],
                }),
                encoding="utf-8",
            )

            with patch(
                "gui.widgets.coding_value.coding_value_panel.EXPORT_CODING_FILES_DIR",
                export_dir,
            ):
                panel = CodingValuePanel()
                self.addCleanup(panel.deleteLater)
                panel.cmb_coding_json.setCurrentIndex(
                    panel.cmb_coding_json.findText("existing")
                )
                panel.file_path.clear()

                with patch(
                    "gui.widgets.coding_value.coding_value_panel.QMessageBox.warning"
                ) as warning:
                    panel.import_coding_value()

        warning.assert_not_called()
        self.assertEqual(panel.table.rowCount(), 1)
        self.assertEqual(panel.table.item(0, 0).text(), "Method Type")
    def test_import_coding_excel_refreshes_json_drop_list_and_loads_table_from_json(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Vehicle Name",
            13,
            0,
            8,
            "0x03=VF3\n0x09=VF7NP",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            export_dir = Path(tmpdir) / "config" / "export_coding_files"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))

            with patch(
                "gui.widgets.coding_value.coding_value_panel.EXPORT_CODING_FILES_DIR",
                export_dir,
            ):
                panel.import_coding_value()

        self.assertEqual(panel.cmb_coding_json.currentText(), "coding")
        self.assertEqual(panel.table.rowCount(), 1)
        self.assertEqual(panel.table.item(0, 0).text(), "Vehicle Name")
        self.assertEqual(panel.table.item(0, 4).text(), "")
        self.assertEqual(panel.table.cellWidget(0, 5).currentText(), "")
    def test_decoded_combobox_options_are_one_item_per_method_type_line(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "$MethodType",
        ])
        sheet.append([
            "Vehicle Variant",
            14,
            0,
            8,
            "\n0x0=Unsupported\n0x1= Comfort\n0x2= Premium\n"
            "0x3= Earth\n0x4= Wind\n0x5=  Sky\n"
            "0x6=  HerioGreen\n0x7=  Reserved\n"
            "0x8 = Reserved\n0x9 = Reserved\n"
            "0xA = Reserved\n0xF=Invalid",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.txt_coding_value.setPlainText("00 " * 14 + "02")
            panel.import_coding_value()

        combo = panel.table.cellWidget(0, 5)
        self.assertEqual(combo.currentText(), "")
        panel.encode_coding_payload()
        self.assertEqual(combo.currentText(), "Premium")
        self.assertEqual(combo.count(), 12)
        self.assertFalse(combo.isEditable())
        self.assertEqual(combo.maxVisibleItems(), 5)
        self.assertEqual(combo.itemText(1), "Comfort")
        self.assertEqual(combo.itemText(2), "Premium")
        self.assertIn(
            "QScrollBar:vertical",
            combo.view().verticalScrollBar().styleSheet(),
        )
        self.assertGreaterEqual(
            panel.table.rowHeight(0),
            combo.sizeHint().height(),
        )

    def test_raw_value_edit_formats_by_bit_length_and_rejects_overflow(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Two Byte Value",
            13,
            0,
            16,
            "0x123=Small\n0x1234=Large",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.txt_coding_value.setPlainText("00 " * 13 + "12 34")
            panel.import_coding_value()
            panel.encode_coding_payload()

        raw_item = panel.table.item(0, 4)
        combo = panel.table.cellWidget(0, 5)

        self.assertTrue(raw_item.flags() & Qt.ItemIsEditable)
        self.assertEqual(raw_item.text(), "12 34")
        self.assertEqual(combo.currentText(), "Large")

        raw_item.setText("123")
        self.assertEqual(raw_item.text(), "01 23")
        self.assertEqual(combo.currentText(), "Small")

        with patch(
            "gui.widgets.coding_value.coding_value_table.QMessageBox.warning"
        ) as warning:
            raw_item.setText("1 00 00")

        warning.assert_called_once()
        self.assertEqual(raw_item.text(), "01 23")
        self.assertEqual(combo.currentText(), "Small")

    def test_raw_value_keeps_two_hex_digits_for_nibble_values(self):
        self.assertEqual(
            CodingValueTable._normalize_user_raw_value("03", 4),
            "03",
        )
        self.assertEqual(
            CodingValueTable._normalize_user_raw_value("1", 4),
            "01",
        )
        self.assertEqual(
            CodingValueTable._normalize_user_raw_value("D", 4),
            "0D",
        )
        self.assertIsNone(
            CodingValueTable._normalize_user_raw_value("10", 4),
        )

    def test_raw_value_accepts_multiple_nibble_tokens_when_bit_length_is_text(self):
        self.assertEqual(
            CodingValueTable._normalize_user_raw_value("08", "4.0"),
            "08",
        )
        self.assertEqual(
            CodingValueTable._normalize_user_raw_value("08 09", "4.0"),
            "08 09",
        )
        self.assertEqual(
            CodingValueTable._normalize_user_raw_value("8 9", "4 bit"),
            "08 09",
        )
        self.assertIsNone(
            CodingValueTable._normalize_user_raw_value("10 09", "4 bit"),
        )

    def test_encode_payload_buttons_update_raw_values_by_byte_position(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Vehicle Name",
            3,
            0,
            8,
            "0x37=Seven\n0xFF=Invalid",
        ])
        sheet.append([
            "Two Byte Value",
            4,
            0,
            16,
            "0x4A39=Name",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.txt_coding_value.setPlainText("62 F1 08 00 00 00")
            panel.import_coding_value()
            panel.txt_coding_value.setPlainText("62 F1 08 37 4A 39")
            panel.encode_coding_payload()

        self.assertEqual(panel.table.item(0, 4).text(), "37")
        self.assertEqual(panel.table.cellWidget(0, 5).currentText(), "Seven")
        self.assertEqual(panel.table.item(1, 4).text(), "4A 39")
        self.assertEqual(panel.table.cellWidget(1, 5).currentText(), "Name")

    def test_encode_payload_splits_bit_fields_by_bit_position(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Byte 17 Low Nibble",
            17,
            0,
            4,
            "0x2=Low",
        ])
        sheet.append([
            "Byte 17 High Nibble",
            17,
            4,
            4,
            "0x1=High",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.txt_coding_value.setPlainText("00 " * 18)
            panel.import_coding_value()
            panel.txt_coding_value.setPlainText("00 " * 17 + "12")
            panel.encode_coding_payload()

        self.assertEqual(panel.table.item(0, 4).text(), "02")
        self.assertEqual(panel.table.cellWidget(0, 5).currentText(), "Low")
        self.assertEqual(panel.table.item(1, 4).text(), "01")
        self.assertEqual(panel.table.cellWidget(1, 5).currentText(), "High")

    def test_payload_copy_and_clear_buttons(self):
        panel = CodingValuePanel()
        self.addCleanup(panel.deleteLater)
        panel.txt_coding_value.setPlainText("62 F1 08")

        panel.copy_coding_payload()
        self.assertEqual(
            QApplication.clipboard().text(),
            "62 F1 08",
        )

        panel.clear_coding_payload()
        self.assertEqual(panel.txt_coding_value.toPlainText(), "")

    def test_payload_input_and_actions_share_one_compact_row(self):
        panel = CodingValuePanel()
        self.addCleanup(panel.deleteLater)

        payload_layout = panel.payload_row.layout()
        input_layout = panel.payload_input_row.layout()
        preview_layout = panel.payload_preview_row.layout()

        self.assertIsInstance(payload_layout, QVBoxLayout)
        self.assertIsInstance(input_layout, QHBoxLayout)
        self.assertIsInstance(preview_layout, QHBoxLayout)
        self.assertEqual(input_layout.indexOf(panel.btn_encode), 0)
        self.assertEqual(input_layout.indexOf(panel.btn_copy), 1)
        self.assertEqual(input_layout.indexOf(panel.btn_clear), 2)
        self.assertEqual(input_layout.indexOf(panel.txt_coding_value), 3)
        self.assertEqual(preview_layout.indexOf(panel.btn_preview_refresh), 0)
        self.assertEqual(preview_layout.indexOf(panel.btn_preview_edit), 1)
        self.assertEqual(preview_layout.indexOf(panel.btn_preview_clear), 2)
        self.assertEqual(preview_layout.indexOf(panel.txt_coding_preview), 3)
        self.assertLessEqual(
            panel.txt_coding_value.maximumHeight(),
            panel.txt_coding_value.fontMetrics().lineSpacing() * 3 + 24,
        )
        self.assertIn(
            "QScrollBar:vertical",
            panel.txt_coding_value.verticalScrollBar().styleSheet(),
        )
        self.assertLessEqual(
            panel.txt_coding_preview.maximumHeight(),
            panel.txt_coding_preview.fontMetrics().lineSpacing() * 3 + 24,
        )
        self.assertIn(
            "QScrollBar:vertical",
            panel.txt_coding_preview.verticalScrollBar().styleSheet(),
        )

    def test_action_buttons_require_payload_data_after_import(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Payload Byte",
            2,
            0,
            8,
            "0x08=Old",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.import_coding_value()

        self.assertFalse(panel.btn_check.isEnabled())
        self.assertFalse(panel.btn_export.isEnabled())
        self.assertFalse(panel.btn_table_copy.isEnabled())
        self.assertFalse(panel.btn_table_clear.isEnabled())
        self.assertFalse(panel.btn_preview_edit.isEnabled())
        self.assertFalse(panel.btn_preview_clear.isEnabled())
        self.assertEqual(panel.table.columnCount(), 6)

        panel.check_coding_value()
        self.assertEqual(panel.table.columnCount(), 6)

        panel.txt_coding_value.setPlainText("62 F1 08")
        self.assertTrue(panel.btn_encode.isEnabled())
        self.assertTrue(panel.btn_copy.isEnabled())
        self.assertTrue(panel.btn_clear.isEnabled())
        self.assertFalse(panel.btn_check.isEnabled())

        panel.encode_coding_payload()
        self.assertTrue(panel.btn_check.isEnabled())
        self.assertTrue(panel.btn_export.isEnabled())
        self.assertTrue(panel.btn_table_copy.isEnabled())
        self.assertTrue(panel.btn_table_clear.isEnabled())
        self.assertFalse(panel.btn_preview_edit.isEnabled())
        self.assertTrue(panel.btn_preview_clear.isEnabled())

        panel.check_coding_value()
        self.assertTrue(panel.btn_preview_edit.isEnabled())

        panel.clear_coding_payload()
        self.assertFalse(panel.btn_check.isEnabled())
        self.assertFalse(panel.btn_export.isEnabled())
        self.assertFalse(panel.btn_table_copy.isEnabled())
        self.assertFalse(panel.btn_table_clear.isEnabled())
        self.assertFalse(panel.btn_preview_edit.isEnabled())
        self.assertFalse(panel.btn_preview_clear.isEnabled())
    def test_check_button_shows_fixed_before_columns_from_encoded_baseline(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Encoded Byte",
            2,
            0,
            8,
            "0x08=Old\n0x99=New",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.import_coding_value()

        panel.txt_coding_value.setPlainText("62 F1 08")
        panel.encode_coding_payload()
        panel.table.item(0, 4).setText("99")
        panel.check_coding_value()

        self.assertEqual(panel.table.item(0, 6).text(), "08")
        self.assertEqual(panel.table.item(0, 7).text(), "Old")
        self.assertEqual(panel.table.item(0, 8).text(), "No-M")

    def test_checked_result_updates_but_before_columns_stay_fixed(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Editable Byte",
            2,
            0,
            8,
            "0x08=Old\n0x99=New",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.txt_coding_value.setPlainText("62 F1 08")
            panel.import_coding_value()
            panel.encode_coding_payload()

        panel.check_coding_value()
        combo = panel.table.cellWidget(0, 5)
        combo.setCurrentIndex(combo.findText("New"))

        self.assertEqual(panel.table.item(0, 4).text(), "99")
        self.assertEqual(panel.table.item(0, 6).text(), "08")
        self.assertEqual(panel.table.item(0, 7).text(), "Old")
        self.assertEqual(panel.table.item(0, 8).text(), "No-M")

    def test_check_button_writes_working_log_for_no_match_changes_and_crc(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Vehicle Name",
            13,
            0,
            8,
            "0x09=VF7NP\n0x01=VF5",
        ])
        sheet.append([
            "Method Type",
            14,
            0,
            8,
            "0x06=Heriogreen\n0x05=Sky",
        ])
        sheet.append([
            "Payload CRC Byte",
            66,
            0,
            8,
            "0xA5=A5\n0x12=12",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.txt_coding_value.setPlainText(
                "00 " * 13 + "09 06 " + "00 " * 51 + "A5"
            )
            panel.import_coding_value()
            panel.encode_coding_payload()

        panel.table.cellWidget(0, 5).setCurrentIndex(
            panel.table.cellWidget(0, 5).findText("VF5")
        )
        panel.table.cellWidget(1, 5).setCurrentIndex(
            panel.table.cellWidget(1, 5).findText("Sky")
        )
        panel.table.cellWidget(2, 5).setCurrentIndex(
            panel.table.cellWidget(2, 5).findText("12")
        )
        panel._payload_baseline_bytes[-1] = 0x77
        panel._payload_preview_bytes[-1] = 0x88
        panel.check_coding_value()

        self.assertEqual(
            panel.txt_working_log.toPlainText(),
            "Total No-M: 3\n\n"
            "Changes: Decode value before -> after\n\n"
            "Byte 13: VF7NP -> VF5\n"
            "Byte 14: Heriogreen -> Sky\n"
            "Byte 66: A5 -> 12\n\n"
            "CRC: 77 -> 88",
        )

    def test_parameter_filter_hides_non_matching_rows(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Vehicle Name",
            13,
            0,
            8,
            "0x03=VF3",
        ])
        sheet.append([
            "Method Type",
            14,
            0,
            8,
            "0x06=Heriogreen",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.import_coding_value()

        self.assertEqual(panel.table.rowCount(), 2)
        self.assertEqual(panel.filter_row.layout().indexOf(panel.txt_parameter_filter), 0)

        panel.table.selectRow(1)
        panel.txt_parameter_filter.setText("vehicle")

        self.assertFalse(panel.table.isRowHidden(0))
        self.assertTrue(panel.table.isRowHidden(1))
        self.assertEqual(panel.table.selectedItems(), [])

        panel.txt_parameter_filter.setText("")

        self.assertFalse(panel.table.isRowHidden(0))
        self.assertFalse(panel.table.isRowHidden(1))
    def test_export_button_writes_visible_table_to_coding_value_report(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Vehicle Name",
            13,
            0,
            8,
            "0x03=VF3\n0x09=VF7NP",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            coding_path = Path(tmpdir) / "coding.xlsx"
            report_root = Path(tmpdir) / "report"
            custom_export_path = Path(tmpdir) / "custom_coding_report.xlsx"
            workbook.save(coding_path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(coding_path))
            panel.txt_coding_value.setPlainText(
                "62 F1 08 00 37 4A 39 39 39 37 34 31 26 03"
            )
            panel.import_coding_value()
            panel.encode_coding_payload()
            panel.check_coding_value()

            with patch(
                "gui.widgets.coding_value.coding_value_panel.CODING_VALUE_REPORT_DIR",
                report_root,
            ), patch(
                "gui.widgets.coding_value.coding_value_panel.QFileDialog.getSaveFileName",
                return_value=(str(custom_export_path), "Excel Files (*.xlsx)"),
            ) as save_dialog, patch(
                "gui.widgets.coding_value.coding_value_panel.QMessageBox.information"
            ) as information:
                panel.btn_export.click()

            save_dialog.assert_called_once()
            default_path = Path(save_dialog.call_args.args[2])
            self.assertEqual(default_path.parent.parent, report_root)
            self.assertTrue(default_path.name.startswith("EEIV_report_Coding value_"))
            information.assert_called_once()
            exported_path = Path(information.call_args.args[2].split("\n\n")[1])
            self.assertEqual(exported_path, custom_export_path)
            self.assertTrue(exported_path.exists())
            self.assertEqual(exported_path.suffix, ".xlsx")

            exported = load_workbook(exported_path)
            self.assertEqual(exported.sheetnames, ["Coding value_62 F1 08"])
            exported_sheet = exported["Coding value_62 F1 08"]
            self.assertEqual(
                [cell.value for cell in exported_sheet[1]],
                [
                    "Parameter",
                    "Byte Pos",
                    "Bit Pos",
                    "Bit Lengh",
                    "Raw value",
                    "Decoded Value (Editable)",
                    "Raw value (before)",
                    "Decoded value (before)",
                    "Result",
                ],
            )
            self.assertEqual(exported_sheet.cell(row=2, column=1).value, "Vehicle Name")
            self.assertEqual(exported_sheet.cell(row=2, column=5).value, "03")
            self.assertEqual(exported_sheet.cell(row=2, column=6).value, "VF3")
            self.assertEqual(exported_sheet.cell(row=2, column=9).value, "MATCH")
    def test_export_button_highlights_no_match_rows_with_warning_fill(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Vehicle Name",
            13,
            0,
            8,
            "0x03=VF3\n0x09=VF7NP",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            coding_path = Path(tmpdir) / "coding.xlsx"
            report_root = Path(tmpdir) / "report"
            custom_export_path = Path(tmpdir) / "custom_coding_report.xlsx"
            workbook.save(coding_path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(coding_path))
            panel.txt_coding_value.setPlainText(
                "62 F1 08 00 37 4A 39 39 39 37 34 31 26 03"
            )
            panel.import_coding_value()
            panel.encode_coding_payload()
            panel.table.cellWidget(0, 5).setCurrentIndex(
                panel.table.cellWidget(0, 5).findText("VF7NP")
            )
            panel.check_coding_value()

            with patch(
                "gui.widgets.coding_value.coding_value_panel.CODING_VALUE_REPORT_DIR",
                report_root,
            ), patch(
                "gui.widgets.coding_value.coding_value_panel.QFileDialog.getSaveFileName",
                return_value=(str(custom_export_path), "Excel Files (*.xlsx)"),
            ) as save_dialog, patch(
                "gui.widgets.coding_value.coding_value_panel.QMessageBox.information"
            ) as information:
                panel.btn_export.click()

            exported_path = Path(information.call_args.args[2].split("\n\n")[1])
            exported = load_workbook(exported_path)
            exported_sheet = exported["Coding value_62 F1 08"]
            warning = ThemeManager.fn_colors().WARNING.replace("#", "").upper()

            self.assertEqual(exported_sheet.cell(row=2, column=9).value, "No-M")
            for cell in exported_sheet[2]:
                self.assertEqual(cell.fill.fill_type, "solid")
                self.assertTrue(cell.fill.fgColor.rgb.upper().endswith(warning))

    def test_table_copy_button_copies_raw_values_and_shows_timed_message(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Payload Byte 2",
            2,
            0,
            8,
            "0x08=Old",
        ])
        sheet.append([
            "Two Byte Value",
            3,
            0,
            16,
            "0x374A=Name",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.txt_coding_value.setPlainText("62 F1 08 37 4A")
            panel.import_coding_value()
            panel.encode_coding_payload()

        with patch.object(panel, "_show_auto_close_information") as information:
            panel.btn_table_copy.click()

        self.assertEqual(QApplication.clipboard().text(), "08 37 4A")
        self.assertEqual(
            panel._copy_raw_value_tokens("4a39"),
            ["4A", "39"],
        )
        information.assert_called_once_with(
            "Coding value",
            "Copy thanh cong:\n\n08 37 4A",
            5000,
        )

    def test_auto_close_information_uses_configurable_timeout(self):
        panel = CodingValuePanel()
        self.addCleanup(panel.deleteLater)

        with patch(
            "gui.widgets.coding_value.coding_value_panel.QMessageBox"
        ) as message_box_class, patch(
            "gui.widgets.coding_value.coding_value_panel.QTimer.singleShot"
        ) as single_shot:
            message_box = message_box_class.return_value

            panel._show_auto_close_information(
                "Coding value",
                "Copy thanh cong:\n\n08",
                1200,
            )

        message_box_class.assert_called_once_with(panel)
        message_box.setWindowTitle.assert_called_once_with("Coding value")
        message_box.setText.assert_called_once_with("Copy thanh cong:\n\n08")
        single_shot.assert_called_once_with(1200, message_box.accept)
        message_box.exec.assert_called_once()

    def test_table_clear_button_clears_table_and_working_log(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Vehicle Name",
            13,
            0,
            8,
            "0x09=VF7NP\n0x01=VF5",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.txt_coding_value.setPlainText("00 " * 13 + "09")
            panel.import_coding_value()
            panel.encode_coding_payload()

        panel.table.cellWidget(0, 5).setCurrentIndex(
            panel.table.cellWidget(0, 5).findText("VF5")
        )
        panel.check_coding_value()
        self.assertEqual(panel.table.item(0, 4).text(), "01")
        self.assertEqual(panel.table.item(0, 6).text(), "09")
        self.assertEqual(panel.table.item(0, 7).text(), "VF7NP")
        self.assertEqual(panel.table.item(0, 8).text(), "No-M")
        self.assertNotEqual(panel.txt_working_log.toPlainText(), "")

        panel.btn_table_clear.click()

        self.assertEqual(panel.table.rowCount(), 0)
        self.assertEqual(panel.txt_working_log.toPlainText(), "")
        self.assertEqual(panel.txt_coding_preview.toPlainText(), "")
        self.assertFalse(panel.btn_check.isEnabled())
        self.assertFalse(panel.btn_table_clear.isEnabled())
    def test_check_button_clears_table_selection(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Selectable Byte",
            2,
            0,
            8,
            "0x08=Old\n0x99=New",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.txt_coding_value.setPlainText("62 F1 08")
            panel.import_coding_value()
            panel.encode_coding_payload()

        panel.table.selectRow(0)
        panel.table.setCurrentCell(0, 4)
        self.assertTrue(panel.table.selectedItems())
        self.assertEqual(panel.table.currentRow(), 0)

        panel.check_coding_value()

        self.assertEqual(panel.table.selectedItems(), [])
        self.assertEqual(panel.table.currentRow(), -1)
        self.assertEqual(panel.table.currentColumn(), -1)
    def test_check_button_adds_before_columns_and_compares_current_values(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Unchanged Byte",
            2,
            0,
            8,
            "0x08=Old\n0x99=New",
        ])
        sheet.append([
            "Changed Byte",
            3,
            0,
            8,
            "0x37=Seven\n0xFF=Invalid",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.txt_coding_value.setPlainText("62 F1 08 37")
            panel.import_coding_value()
            panel.encode_coding_payload()

        panel.check_coding_value()

        headers = [
            panel.table.horizontalHeaderItem(index).text()
            for index in range(panel.table.columnCount())
        ]
        self.assertEqual(headers[-3:], [
            "Raw value (before)",
            "Decoded value (before)",
            "Result",
        ])
        self.assertEqual(panel.table.item(0, 6).text(), "08")
        self.assertEqual(panel.table.item(0, 7).text(), "Old")
        self.assertEqual(panel.table.item(0, 8).text(), "MATCH")
        self.assertEqual(
            panel.table.item(0, 8).background().color().name().upper(),
            ThemeManager.fn_colors().SUCCESS.upper(),
        )
        self.assertEqual(panel.table.item(1, 6).text(), "37")
        self.assertEqual(panel.table.item(1, 7).text(), "Seven")
        self.assertEqual(panel.table.item(1, 8).text(), "MATCH")

        panel.table.item(1, 4).setText("FF")
        self.assertEqual(panel.table.item(1, 6).text(), "37")
        self.assertEqual(panel.table.item(1, 7).text(), "Seven")
        self.assertEqual(panel.table.item(1, 8).text(), "No-M")
        self.assertEqual(
            panel.table.item(1, 8).background().color().name().upper(),
            ThemeManager.fn_colors().WARNING.upper(),
        )

        panel.check_coding_value()
        self.assertEqual(panel.table.columnCount(), 9)
    def test_table_uses_compact_widths_and_elides_overflow_text(self):
        table = CodingValueTable()
        self.addCleanup(table.deleteLater)

        self.assertEqual(table.textElideMode(), Qt.ElideRight)
        self.assertEqual(table.columnWidth(0), table.columnWidth(5))
        self.assertLess(table.columnWidth(1), table.columnWidth(0))
        self.assertLess(table.columnWidth(2), table.columnWidth(0))
        self.assertLess(table.columnWidth(3), table.columnWidth(0))
        self.assertLess(table.columnWidth(4), table.columnWidth(0))

        table.apply_check_results()

        self.assertGreater(table.columnWidth(7), table.columnWidth(1))
        self.assertLess(table.columnWidth(7), table.columnWidth(0))
        self.assertEqual(
            table.horizontalHeader().sectionResizeMode(7),
            QHeaderView.Stretch,
        )
    def test_table_has_right_side_actions_and_working_log_layout(self):
        panel = CodingValuePanel()
        self.addCleanup(panel.deleteLater)

        table_area_layout = panel.table_area.layout()
        side_layout = panel.table_side_panel.layout()
        action_layout = panel.table_action_panel.layout()

        self.assertIsInstance(table_area_layout, QHBoxLayout)
        self.assertEqual(table_area_layout.indexOf(panel.table), 0)
        self.assertEqual(table_area_layout.indexOf(panel.table_side_panel), 1)
        self.assertIsInstance(side_layout, QVBoxLayout)
        self.assertEqual(side_layout.indexOf(panel.table_action_panel), 0)
        self.assertEqual(side_layout.indexOf(panel.txt_working_log), 1)
        self.assertIsInstance(action_layout, QVBoxLayout)
        self.assertEqual(action_layout.indexOf(panel.btn_check), 0)
        self.assertEqual(action_layout.indexOf(panel.btn_export), 1)
        self.assertEqual(action_layout.indexOf(panel.btn_table_copy), 2)
        self.assertEqual(action_layout.indexOf(panel.btn_table_clear), 3)
        self.assertTrue(panel.txt_working_log.isReadOnly())
        self.assertIn(
            "QScrollBar:vertical",
            panel.txt_working_log.verticalScrollBar().styleSheet(),
        )
    def test_payload_preview_updates_and_highlights_table_raw_changes(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Vehicle Name",
            3,
            0,
            8,
            "0x37=Seven\n0xFF=Invalid",
        ])
        sheet.append([
            "Byte 4 Low Nibble",
            4,
            0,
            4,
            "0x2=Low\n0x5=Changed",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.txt_coding_value.setPlainText("62 F1 08 37 12")
            panel.import_coding_value()
            panel.encode_coding_payload()

        self.assertIsInstance(panel.txt_coding_preview, QPlainTextEdit)
        self.assertTrue(panel.txt_coding_preview.isReadOnly())
        self.assertEqual(
            panel.txt_coding_preview.toPlainText(),
            "62 F1 08 37 12",
        )

        panel.table.item(0, 4).setText("FF")
        self.assertEqual(
            panel.txt_coding_preview.toPlainText(),
            "62 F1 08 FF 12",
        )
        self.assertEqual(len(panel.txt_coding_preview.extraSelections()), 1)

        panel.table.item(1, 4).setText("05")
        self.assertEqual(
            panel.txt_coding_preview.toPlainText(),
            "62 F1 08 FF 15",
        )
        self.assertEqual(len(panel.txt_coding_preview.extraSelections()), 1)

    def test_preview_edit_imports_payload_after_check_without_resetting_before(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Editable Byte",
            2,
            0,
            8,
            "0x08=Old\n0x99=New",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.txt_coding_value.setPlainText("62 F1 08")
            panel.import_coding_value()
            panel.encode_coding_payload()

        self.assertEqual(panel.btn_preview_edit.text(), "EDIT")
        self.assertFalse(panel.btn_preview_edit.isEnabled())
        self.assertTrue(panel.txt_coding_preview.isReadOnly())

        panel.check_coding_value()
        self.assertTrue(panel.btn_preview_edit.isEnabled())

        panel.btn_preview_edit.click()
        self.assertFalse(panel.txt_coding_preview.isReadOnly())
        self.assertEqual(panel.btn_preview_edit.text(), "IMPORT")

        panel.txt_coding_preview.setPlainText("62 F1 99")
        panel.btn_preview_edit.click()

        self.assertTrue(panel.txt_coding_preview.isReadOnly())
        self.assertEqual(panel.btn_preview_edit.text(), "EDIT")
        self.assertEqual(panel.table.item(0, 4).text(), "99")
        self.assertEqual(panel.table.cellWidget(0, 5).currentText(), "New")
        self.assertEqual(panel.table.item(0, 6).text(), "08")
        self.assertEqual(panel.table.item(0, 7).text(), "Old")
        self.assertEqual(panel.table.item(0, 8).text(), "No-M")
        self.assertEqual(panel._payload_baseline_bytes, [0x62, 0xF1, 0x08])
        self.assertEqual(panel._payload_preview_bytes, [0x62, 0xF1, 0x99])

    def test_payload_preview_refresh_copy_and_clear_buttons(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append([
            "Parameter",
            "BytePos (from 0)",
            "BitPos",
            "BitLength",
            "MethodType",
        ])
        sheet.append([
            "Payload Byte 2",
            2,
            0,
            8,
            "0x08=Old\n0x99=New",
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coding.xlsx"
            workbook.save(path)

            panel = CodingValuePanel()
            self.addCleanup(panel.deleteLater)
            panel.file_path.setText(str(path))
            panel.txt_coding_value.setPlainText("62 F1 08")
            panel.import_coding_value()
            panel.encode_coding_payload()

        self.assertEqual(panel.table.item(0, 4).text(), "08")
        panel.txt_coding_value.setPlainText("62 F1 99")

        panel.refresh_coding_preview()
        self.assertEqual(panel.table.item(0, 4).text(), "99")
        self.assertEqual(
            panel.txt_coding_preview.toPlainText(),
            "62 F1 99",
        )

        panel.clear_coding_preview()
        self.assertEqual(panel.txt_coding_preview.toPlainText(), "")
        self.assertEqual(panel._payload_preview_bytes, [])


if __name__ == "__main__":
    unittest.main()

