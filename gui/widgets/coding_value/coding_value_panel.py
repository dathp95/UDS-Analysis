from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from openpyxl import Workbook

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPlainTextEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config.paths import REPORT_DIR
from core.coding_value import load_coding_value_rows
from gui.themes.styles.containers.groupbox_style import fn_groupbox_style
from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style
from gui.widgets.coding_value.coding_value_table import CodingValueTable
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_lineedit import PrimaryLineEdit


DEFAULT_CODING_DIR = Path("config/Coding")
DEFAULT_CODING_FILE = DEFAULT_CODING_DIR / "MHU CDS Coding.xlsx"


class CodingValuePanel(QGroupBox):

    def __init__(self):
        super().__init__("Coding Value")

        self._payload_preview_bytes = []
        self._payload_baseline_bytes = []
        self._has_encoded_payload = False
        self._setup_ui()
        self._connect_signals()
        self.fn_refresh_theme()

    def _setup_ui(self):
        self.content = QWidget()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            12,
            14,
            12,
            12,
        )
        layout.setSpacing(8)

        self.file_path = PrimaryLineEdit(
            placeholder="Select coding Excel file"
        )
        self.file_path.setText(
            str(DEFAULT_CODING_FILE)
        )
        self.btn_browse = PrimaryButton(
            "Browse",
            width=100,
        )
        self.btn_import = PrimaryButton(
            "Import",
            width=100,
        )

        file_layout = QHBoxLayout()
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.setSpacing(8)
        file_layout.addWidget(self.file_path, 1)
        file_layout.addWidget(self.btn_browse)
        file_layout.addWidget(self.btn_import)

        self.txt_coding_value = QPlainTextEdit()
        self.txt_coding_value.setPlaceholderText(
            "Paste coding value payload here"
        )
        self.txt_coding_value.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.txt_coding_preview = QPlainTextEdit()
        self.txt_coding_preview.setPlaceholderText(
            "Coding payload preview"
        )
        self.txt_coding_preview.setReadOnly(True)
        self.txt_coding_preview.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self._set_payload_editor_height()

        self.btn_encode = PrimaryButton(
            "Encode",
            width=100,
        )
        self.btn_copy = PrimaryButton(
            "Copy",
            width=100,
        )
        self.btn_clear = PrimaryButton(
            "Clear",
            width=100,
        )
        self.btn_preview_refresh = PrimaryButton(
            "Refresh",
            width=100,
        )
        self.btn_preview_copy = PrimaryButton(
            "Copy",
            width=100,
        )
        self.btn_preview_clear = PrimaryButton(
            "Clear",
            width=100,
        )

        self.payload_input_row = QWidget()
        input_layout = QHBoxLayout(self.payload_input_row)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)
        input_layout.addWidget(self.btn_encode, 0, Qt.AlignTop)
        input_layout.addWidget(self.btn_copy, 0, Qt.AlignTop)
        input_layout.addWidget(self.btn_clear, 0, Qt.AlignTop)
        input_layout.addWidget(self.txt_coding_value, 1)

        self.payload_preview_row = QWidget()
        preview_layout = QHBoxLayout(self.payload_preview_row)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(8)
        preview_layout.addWidget(self.btn_preview_refresh, 0, Qt.AlignTop)
        preview_layout.addWidget(self.btn_preview_copy, 0, Qt.AlignTop)
        preview_layout.addWidget(self.btn_preview_clear, 0, Qt.AlignTop)
        preview_layout.addWidget(self.txt_coding_preview, 1)

        self.payload_row = QWidget()
        payload_layout = QVBoxLayout(self.payload_row)
        payload_layout.setContentsMargins(0, 0, 0, 0)
        payload_layout.setSpacing(6)
        payload_layout.addWidget(self.payload_input_row)
        payload_layout.addWidget(self.payload_preview_row)

        self.txt_parameter_filter = PrimaryLineEdit(
            placeholder="Filter parameter"
        )
        self.filter_row = QWidget()
        filter_layout = QHBoxLayout(self.filter_row)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(8)
        filter_layout.addWidget(self.txt_parameter_filter, 1)

        self.table = CodingValueTable()

        self.btn_check = PrimaryButton(
            "CHECK",
            width=110,
        )
        self.btn_export = PrimaryButton(
            "EXPORT",
            width=110,
        )
        self.btn_table_copy = PrimaryButton(
            "COPY",
            width=110,
        )
        self.btn_table_clear = PrimaryButton(
            "CLEAR",
            width=110,
        )

        self.table_action_panel = QWidget()
        action_layout = QVBoxLayout(self.table_action_panel)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)
        action_layout.addWidget(self.btn_check)
        action_layout.addWidget(self.btn_export)
        action_layout.addWidget(self.btn_table_copy)
        action_layout.addWidget(self.btn_table_clear)
        action_layout.addStretch(1)

        self.txt_working_log = QPlainTextEdit()
        self.txt_working_log.setPlaceholderText(
            "Working log"
        )
        self.txt_working_log.setReadOnly(True)
        self.txt_working_log.setMinimumWidth(220)
        self.txt_working_log.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.table_side_panel = QWidget()
        side_layout = QVBoxLayout(self.table_side_panel)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(8)
        side_layout.addWidget(self.table_action_panel, 0)
        side_layout.addWidget(self.txt_working_log, 1)

        self.table_area = QWidget()
        table_area_layout = QHBoxLayout(self.table_area)
        table_area_layout.setContentsMargins(0, 0, 0, 0)
        table_area_layout.setSpacing(8)
        table_area_layout.addWidget(self.table, 1)
        table_area_layout.addWidget(self.table_side_panel, 0)

        layout.addLayout(file_layout)
        layout.addWidget(self.payload_row)
        layout.addWidget(self.filter_row)
        layout.addWidget(self.table_area, 1)

    def _set_payload_editor_height(self):
        self._set_editor_three_line_height(self.txt_coding_value)
        self._set_editor_three_line_height(self.txt_coding_preview)

    @staticmethod
    def _set_editor_three_line_height(editor):
        line_height = editor.fontMetrics().lineSpacing()
        frame_width = editor.frameWidth() * 2
        vertical_padding = 12
        height = line_height * 3 + frame_width + vertical_padding
        editor.setMinimumHeight(height)
        editor.setMaximumHeight(height)

    def _connect_signals(self):
        self.btn_browse.clicked.connect(
            self.browse_file
        )
        self.btn_import.clicked.connect(
            self.import_coding_value
        )
        self.btn_encode.clicked.connect(
            self.encode_coding_payload
        )
        self.btn_copy.clicked.connect(
            self.copy_coding_payload
        )
        self.btn_clear.clicked.connect(
            self.clear_coding_payload
        )
        self.btn_preview_refresh.clicked.connect(
            self.refresh_coding_preview
        )
        self.btn_preview_copy.clicked.connect(
            self.copy_coding_preview
        )
        self.btn_preview_clear.clicked.connect(
            self.clear_coding_preview
        )
        self.btn_check.clicked.connect(
            self.check_coding_value
        )
        self.btn_export.clicked.connect(
            self.export_coding_value
        )
        self.btn_table_clear.clicked.connect(
            self.clear_table_coding_values
        )
        self.table.raw_value_changed.connect(
            self.update_payload_preview_from_raw
        )
        self.txt_parameter_filter.textChanged.connect(
            self.filter_parameter_table
        )
        self.txt_coding_value.textChanged.connect(
            self._update_action_states
        )

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Coding Excel",
            str(DEFAULT_CODING_DIR),
            "Excel Files (*.xlsx *.xlsm *.xltx *.xltm)",
        )

        if file_path:
            self.file_path.setText(file_path)

    def import_coding_value(self):
        excel_path = self.file_path.text().strip()
        if not excel_path:
            QMessageBox.warning(
                self,
                "Coding value",
                "Please select a coding Excel file before importing.",
            )
            return

        try:
            rows = load_coding_value_rows(
                excel_path,
                "",
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Coding value",
                f"Cannot import coding Excel file:\n{exc}",
            )
            return

        self.table.set_rows(rows)
        self.filter_parameter_table()
        self.clear_coding_preview()
        self._update_action_states()

    def filter_parameter_table(self):
        self.table.filter_by_parameter(
            self.txt_parameter_filter.text()
        )
    def encode_coding_payload(self):
        self._encode_payload_to_table(
            warn_when_empty=True,
            warn_when_no_rows=True,
        )

    def _encode_payload_to_table(
            self,
            warn_when_empty=False,
            warn_when_no_rows=False,
        ):
        payload = self.txt_coding_value.toPlainText()
        if not payload.strip():
            if warn_when_empty:
                QMessageBox.warning(
                    self,
                    "Coding value",
                    "Please input coding value payload before encoding.",
                )
            self._update_action_states()
            return 0

        updated = self.table.encode_payload(payload)
        if updated > 0:
            self.set_payload_preview(payload)
            self._has_encoded_payload = True
        elif warn_when_no_rows:
            QMessageBox.warning(
                self,
                "Coding value",
                "No raw value row could be updated from this payload.",
            )
        self._update_action_states()
        return updated

    def check_coding_value(self):
        if not self._can_use_table_actions():
            return

        self.table.apply_check_results()
        self._write_check_working_log()

    def export_coding_value(self):
        if not self._can_use_table_actions():
            return

        try:
            output_file = self._export_coding_report()
        except PermissionError:
            QMessageBox.warning(
                self,
                "Coding value",
                "Cannot save Coding value report. Please close the Excel file and try again.",
            )
            return

        QMessageBox.information(
            self,
            "Coding value",
            f"Coding value report saved:\n\n{output_file}",
        )

    def _export_coding_report(self):
        now = datetime.now()
        report_folder = REPORT_DIR / now.strftime("%d-%m-%Y")
        report_folder.mkdir(
            parents=True,
            exist_ok=True,
        )
        output_file = report_folder / (
            f"EEIV_report_Coding value_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = self._coding_export_sheet_name()
        sheet.append(self._coding_table_headers())
        for row_index in range(self.table.rowCount()):
            if self.table.isRowHidden(row_index):
                continue

            sheet.append(
                self._coding_table_row_values(row_index)
            )

        workbook.save(output_file)
        return output_file

    def _coding_export_sheet_name(self):
        return self._safe_excel_sheet_name(
            f"Coding value_{self._coding_export_identifier()}"
        )

    def _coding_export_identifier(self):
        payload_bytes = self._payload_baseline_bytes or self._payload_preview_bytes
        return " ".join(
            f"{value:02X}"
            for value in payload_bytes[:3]
        )

    def _coding_table_headers(self):
        return [
            self.table.horizontalHeaderItem(column).text()
            for column in range(self.table.columnCount())
        ]

    def _coding_table_row_values(self, row_index):
        values = []
        for column in range(self.table.columnCount()):
            widget = self.table.cellWidget(row_index, column)
            if hasattr(widget, "currentText"):
                values.append(widget.currentText())
                continue

            item = self.table.item(row_index, column)
            values.append(item.text() if item is not None else "")

        return values

    @staticmethod
    def _safe_excel_sheet_name(name):
        invalid_chars = r'[]:*?/\\'
        for char in invalid_chars:
            name = name.replace(char, "_")

        return name[:31] or "Coding value"
    def copy_coding_payload(self):
        QApplication.clipboard().setText(
            self.txt_coding_value.toPlainText()
        )

    def clear_coding_payload(self):
        self.txt_coding_value.clear()
        self.clear_coding_preview()

    def clear_table_coding_values(self):
        self.table.clear_rows()
        self.txt_working_log.clear()
        self.clear_coding_preview()

    def refresh_coding_preview(self):
        if self._encode_payload_to_table() == 0:
            self.set_payload_preview(
                self.txt_coding_value.toPlainText()
            )

    def copy_coding_preview(self):
        QApplication.clipboard().setText(
            self.txt_coding_preview.toPlainText()
        )

    def clear_coding_preview(self):
        self.txt_coding_preview.clear()
        self.txt_coding_preview.setExtraSelections([])
        self._payload_preview_bytes = []
        self._payload_baseline_bytes = []
        self._has_encoded_payload = False
        self._update_action_states()

    def _update_action_states(self):
        has_input_payload = bool(self.txt_coding_value.toPlainText().strip())
        has_preview_payload = bool(self.txt_coding_preview.toPlainText().strip())
        has_table_rows = self.table.rowCount() > 0
        can_encode = has_table_rows and has_input_payload
        can_use_preview = has_preview_payload
        can_use_table_actions = self._can_use_table_actions()

        self.btn_encode.setEnabled(can_encode)
        self.btn_copy.setEnabled(has_input_payload)
        self.btn_clear.setEnabled(has_input_payload)
        self.btn_preview_refresh.setEnabled(can_encode)
        self.btn_preview_copy.setEnabled(can_use_preview)
        self.btn_preview_clear.setEnabled(can_use_preview)
        self.btn_check.setEnabled(can_use_table_actions)
        self.btn_export.setEnabled(can_use_table_actions)
        self.btn_table_copy.setEnabled(can_use_table_actions)
        self.btn_table_clear.setEnabled(can_use_table_actions)

    def _can_use_table_actions(self):
        return (
            self._has_encoded_payload
            and self.table.rowCount() > 0
            and bool(self._payload_preview_bytes)
        )

    def _write_check_working_log(self):
        self.txt_working_log.setPlainText(
            self._build_check_working_log()
        )

    def _build_check_working_log(self):
        changes = []
        for row_index in range(self.table.rowCount()):
            result_item = self.table.item(row_index, 8)
            if result_item is None or result_item.text() != "No-M":
                continue

            byte_item = self.table.item(row_index, 1)
            before_decoded_item = self.table.item(row_index, 7)
            current_raw_item = self.table.item(row_index, 4)
            current_raw = current_raw_item.text() if current_raw_item else ""
            byte_text = byte_item.text() if byte_item else str(row_index)
            before_decoded = (
                before_decoded_item.text()
                if before_decoded_item is not None
                else ""
            )
            after_decoded = self.table._decoded_text_for_raw(
                row_index,
                current_raw,
            )
            changes.append(
                f"Byte {byte_text}: {before_decoded} -> {after_decoded}"
            )

        lines = [
            f"Total No-M: {len(changes)}",
            "",
            "Changes: Decode value before -> after",
            "",
        ]
        lines.extend(changes)
        lines.extend([
            "",
            (
                "CRC: "
                f"{self._crc_text(self._payload_baseline_bytes)} -> "
                f"{self._crc_text(self._payload_preview_bytes)}"
            ),
        ])
        return "\n".join(lines)

    @staticmethod
    def _crc_text(payload_bytes):
        if not payload_bytes:
            return ""

        return f"{payload_bytes[-1]:02X}"

    def set_payload_preview(self, payload):
        self._payload_preview_bytes = self.table._parse_payload_bytes(payload)
        self._payload_baseline_bytes = list(self._payload_preview_bytes)
        self.txt_coding_preview.setPlainText(
            self._format_payload_bytes(self._payload_preview_bytes)
        )
        self.txt_coding_preview.setExtraSelections([])

    def update_payload_preview_from_raw(
            self,
            _row_index,
            byte_pos,
            bit_pos,
            bit_length,
            raw_value,
        ):
        changed_bytes = self._apply_raw_to_payload_bytes(
            byte_pos,
            bit_pos,
            bit_length,
            raw_value,
        )
        if not changed_bytes:
            return

        self.txt_coding_preview.setPlainText(
            self._format_payload_bytes(self._payload_preview_bytes)
        )
        self._highlight_payload_bytes(changed_bytes)

    def _apply_raw_to_payload_bytes(
            self,
            byte_pos,
            bit_pos,
            bit_length,
            raw_value,
        ):
        if byte_pos < 0 or byte_pos >= len(self._payload_preview_bytes):
            return []

        tokens = self.table._hex_tokens(raw_value)
        if not tokens:
            return []

        raw_int = int("".join(tokens), 16)
        if bit_pos == 0 and bit_length % 8 == 0:
            byte_count = bit_length // 8
            if byte_count <= 0 or byte_pos + byte_count > len(self._payload_preview_bytes):
                return []
            raw_bytes = raw_int.to_bytes(byte_count, byteorder="big")
            for offset, value in enumerate(raw_bytes):
                self._payload_preview_bytes[byte_pos + offset] = value
            return list(range(byte_pos, byte_pos + byte_count))

        byte_count = (bit_pos + bit_length + 7) // 8
        if byte_count <= 0 or byte_pos + byte_count > len(self._payload_preview_bytes):
            return []

        selected = self._payload_preview_bytes[byte_pos:byte_pos + byte_count]
        container = int.from_bytes(bytes(selected), byteorder="little")
        mask = ((1 << bit_length) - 1) << bit_pos
        container = (container & ~mask) | ((raw_int << bit_pos) & mask)
        merged = container.to_bytes(byte_count, byteorder="little")
        for offset, value in enumerate(merged):
            self._payload_preview_bytes[byte_pos + offset] = value
        return list(range(byte_pos, byte_pos + byte_count))

    @staticmethod
    def _format_payload_bytes(payload_bytes):
        return " ".join(
            f"{value:02X}"
            for value in payload_bytes
        )

    def _highlight_payload_bytes(self, byte_indexes):
        selections = []
        color = QColor("#FFE08A")
        for byte_index in byte_indexes:
            start = byte_index * 3
            cursor = QTextCursor(self.txt_coding_preview.document())
            cursor.setPosition(start)
            cursor.movePosition(
                QTextCursor.Right,
                QTextCursor.KeepAnchor,
                2,
            )
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format = QTextCharFormat()
            selection.format.setBackground(color)
            selections.append(selection)

        self.txt_coding_preview.setExtraSelections(selections)

    def fn_refresh_theme(self):
        self.setStyleSheet(
            fn_groupbox_style()
        )
        self.file_path.fn_refresh_theme()
        self.txt_parameter_filter.fn_refresh_theme()
        self.btn_browse.fn_refresh_theme()
        self.btn_import.fn_refresh_theme()
        self.btn_encode.fn_refresh_theme()
        self.btn_copy.fn_refresh_theme()
        self.btn_clear.fn_refresh_theme()
        self.btn_preview_refresh.fn_refresh_theme()
        self.btn_preview_copy.fn_refresh_theme()
        self.btn_preview_clear.fn_refresh_theme()
        self.btn_check.fn_refresh_theme()
        self.btn_export.fn_refresh_theme()
        self.btn_table_copy.fn_refresh_theme()
        self.btn_table_clear.fn_refresh_theme()
        self.table.fn_refresh_theme()
        self._update_action_states()
        fn_apply_scrollbar_style(
            self.txt_coding_value
        )
        fn_apply_scrollbar_style(
            self.txt_coding_preview
        )
        fn_apply_scrollbar_style(
            self.txt_working_log
        )

