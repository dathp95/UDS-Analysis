from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHeaderView,
    QMessageBox,
)

from gui.themes.styles.controls.scrollbar_style import (
    fn_apply_scrollbar_style,
)
from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.primary_combobox import PrimaryComboBox
from gui.widgets.controls.primary_table import PrimaryTable
from core.coding_value_payload import (
    extract_raw_value,
    format_raw_int,
    format_raw_value,
    hex_tokens,
    is_spaced_hex,
    normalize_raw_tokens,
    normalize_user_raw_value,
    parse_payload_text,
    to_int,
)


class CodingValueTable(PrimaryTable):

    raw_value_changed = Signal(int, int, int, int, str)
    HEADERS = [
        "Parameter",
        "Byte Pos",
        "Bit Pos",
        "Bit Lengh",
        "Raw value",
        "Decoded Value (Editable)",
    ]
    CHECK_HEADERS = [
        "Raw value (before)",
        "Decoded value (before)",
        "Result",
    ]
    COLUMN_WIDTHS = {
        0: 240,
        1: 64,
        2: 58,
        3: 74,
        4: 82,
        5: 240,
        6: 96,
        7: 112,
        8: 72,
    }

    def __init__(self):
        super().__init__()

        self._row_state = {}
        self._syncing_raw_value = False
        self._setup_table()

    def _setup_table(self):
        self.setSortingEnabled(False)
        self.setEditTriggers(
            QAbstractItemView.DoubleClicked
            | QAbstractItemView.EditKeyPressed
            | QAbstractItemView.SelectedClicked
        )
        self.itemChanged.connect(self._handle_item_changed)
        self.setTextElideMode(Qt.ElideRight)

        self.setColumnCount(
            len(self.HEADERS)
        )
        self.setHorizontalHeaderLabels(
            self.HEADERS
        )

        header = self.horizontalHeader()
        header.setSectionResizeMode(
            QHeaderView.Interactive
        )
        header.setStretchLastSection(False)

        self._apply_column_widths()
        self.verticalHeader().setDefaultSectionSize(40)

    def set_rows(self, rows):
        self._syncing_raw_value = True
        self._row_state = {}
        self.setColumnCount(len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setRowCount(
            len(rows)
        )

        for row_index, row in enumerate(rows):
            raw_value = ""
            self._row_state[row_index] = {
                "bit_length": self._to_int(row.bit_length),
                "bit_pos": self._to_int(row.bit_pos),
                "byte_pos": row.byte_pos,
                "byte_pos_int": self._to_int(row.byte_pos),
                "last_raw": raw_value,
                "original_raw": raw_value,
            }
            values = [
                row.parameter,
                row.byte_pos,
                row.bit_pos,
                row.bit_length,
                raw_value,
            ]

            for column, value in enumerate(values):
                item = self.fn_create_item(
                    value,
                    row_index,
                )
                if column == 4:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                self.setItem(
                    row_index,
                    column,
                    item,
                )

            self.setCellWidget(
                row_index,
                5,
                self._create_decoded_combo(row_index, row),
            )
            self.setRowHeight(row_index, 40)

        self._syncing_raw_value = False

    def clear_rows(self):
        self._row_state = {}
        self.setRowCount(0)

    def fn_find_row_index_by_parameter(self, parameter_keyword):
        keyword = str(parameter_keyword or "").strip().lower()
        if not keyword:
            return -1

        for row_index in range(self.rowCount()):
            item = self.item(row_index, 0)
            parameter = item.text().strip().lower() if item is not None else ""
            if keyword in parameter:
                return row_index

        return -1

    def fn_payload_location_for_row(self, row_index):
        state = self._row_state.get(row_index, {})
        return (
            state.get("byte_pos_int"),
            state.get("bit_pos"),
            state.get("bit_length"),
        )

    def fn_set_raw_value_at_row(
            self,
            row_index,
            raw_value,
            emit_raw_change=True,
        ):
        if row_index < 0 or row_index >= self.rowCount():
            return False

        return self._apply_raw_value_to_row(
            row_index,
            raw_value,
            emit_raw_change=emit_raw_change,
        )

    def fn_set_raw_value_by_parameter(
            self,
            parameter_keyword,
            raw_value,
            emit_raw_change=True,
        ):
        row_index = self.fn_find_row_index_by_parameter(parameter_keyword)
        if row_index < 0:
            return False

        return self.fn_set_raw_value_at_row(
            row_index,
            raw_value,
            emit_raw_change=emit_raw_change,
        )

    def filter_by_parameter(self, keyword):
        text = str(keyword or "").strip().lower()
        for row_index in range(self.rowCount()):
            row_text = " ".join((
                self._cell_text(row_index, 0),
                self._cell_text(row_index, 8),
            )).lower()
            self.setRowHidden(
                row_index,
                bool(text) and text not in row_text,
            )

        self.clearSelection()
        self.setCurrentCell(-1, -1)

    def _cell_text(self, row_index, column):
        if column >= self.columnCount():
            return ""

        item = self.item(row_index, column)
        return item.text() if item is not None else ""

    def encode_payload(self, payload, update_original=True):
        payload_bytes = self._parse_payload_bytes(payload)
        if not payload_bytes:
            return 0

        updated = 0
        for row_index in range(self.rowCount()):
            state = self._row_state.get(row_index, {})
            byte_pos = state.get("byte_pos_int")
            if byte_pos is None or byte_pos < 0 or byte_pos >= len(payload_bytes):
                continue

            raw_value = self._payload_raw_value(
                payload_bytes,
                byte_pos,
                state.get("bit_pos"),
                state.get("bit_length"),
            )
            if not raw_value:
                continue

            self._set_raw_item_text(
                row_index,
                raw_value,
            )
            state["last_raw"] = raw_value
            if update_original:
                state["original_raw"] = raw_value
            self._sync_decoded_value_from_raw(row_index, raw_value)
            self._update_check_result_if_visible(row_index, raw_value)
            updated += 1

        return updated

    def apply_check_results(self):
        self._ensure_check_columns()
        for row_index in range(self.rowCount()):
            state = self._row_state.get(row_index, {})
            original_raw = state.get("original_raw", "")
            original_decoded = self._decoded_text_for_raw(row_index, original_raw)

            self._set_readonly_item(row_index, 6, original_raw)
            self._set_readonly_item(row_index, 7, original_decoded)
            self._update_check_result(row_index, self._current_raw_value(row_index))

        self.clearSelection()
        self.setCurrentCell(-1, -1)

    def _update_check_result_if_visible(self, row_index, raw_value):
        if self.columnCount() < len(self.HEADERS) + len(self.CHECK_HEADERS):
            return

        self._update_check_result(row_index, raw_value)

    def _update_check_result(self, row_index, current_raw):
        state = self._row_state.get(row_index, {})
        original_raw = state.get("original_raw", "")
        result = "MATCH" if current_raw == original_raw else "No-M"
        self._set_readonly_item(row_index, 8, result)
        self._apply_result_style(row_index, result)

    def _apply_result_style(self, row_index, result):
        item = self.item(row_index, 8)
        if item is None:
            return

        colors = ThemeManager.fn_colors()
        background = colors.SUCCESS if result == "MATCH" else colors.WARNING
        item.setBackground(QColor(background))
        item.setForeground(QColor(colors.TEXT_INVERT))

    def _ensure_check_columns(self):
        headers = self.HEADERS + self.CHECK_HEADERS
        if self.columnCount() < len(headers):
            self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self._apply_column_widths()

    def _apply_column_widths(self):
        header = self.horizontalHeader()
        for column, width in self.COLUMN_WIDTHS.items():
            if column < self.columnCount():
                header.setSectionResizeMode(column, QHeaderView.Interactive)
                self.setColumnWidth(column, width)

        if 7 < self.columnCount():
            header.setSectionResizeMode(7, QHeaderView.Stretch)

    def _set_readonly_item(self, row_index, column, value):
        item = self.item(row_index, column)
        if item is None:
            item = self.fn_create_item(
                str(value),
                row_index,
            )
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.setItem(row_index, column, item)
            return

        item.setText(str(value))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

    def _current_raw_value(self, row_index):
        item = self.item(row_index, 4)
        return item.text() if item is not None else ""

    def _decoded_text_for_raw(self, row_index, raw_value):
        combo = self.cellWidget(row_index, 5)
        if combo is None:
            return raw_value

        for index in range(combo.count()):
            if combo.itemData(index, Qt.UserRole) == raw_value:
                return combo.itemText(index)

        return raw_value

    def _create_decoded_combo(self, row_index, row):
        has_option_list = bool(row.decoded_options)
        combo = self._create_base_decoded_combo(
            not has_option_list,
            5 if has_option_list else 12,
        )

        if row.decoded_options:
            for option in row.decoded_options:
                combo.addItem(
                    option.label,
                    self._format_raw_value(
                        option.raw_value,
                        row.bit_length,
                    ),
                )
        elif row.decoded_value:
            combo.addItem(row.decoded_value)

        if has_option_list:
            combo.setCurrentIndex(-1)
        else:
            combo.setEditText("")

        self._connect_decoded_combo(row_index, combo)

        return combo

    def _create_base_decoded_combo(self, editable, max_visible_items):
        combo = PrimaryComboBox(
            minimum_height=30
        )
        combo.setEditable(editable)
        combo.setMaximumHeight(32)
        combo.setMinimumWidth(0)
        combo.setMinimumContentsLength(0)
        combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        combo.setMaxVisibleItems(max_visible_items)
        combo.view().setTextElideMode(Qt.ElideRight)
        fn_apply_scrollbar_style(combo.view())
        return combo

    def _connect_decoded_combo(self, row_index, combo):
        combo.currentIndexChanged.connect(
            lambda index, row_index=row_index, combo=combo: (
                self._sync_raw_value_from_combo(
                    row_index,
                    combo,
                    index,
                )
            )
        )

    def _sync_raw_value_from_combo(self, row_index, combo, index):
        if self._syncing_raw_value:
            return

        raw_value = combo.itemData(index, Qt.UserRole)
        if raw_value in (None, ""):
            return

        self._apply_raw_value_to_row(row_index, raw_value)

    def _apply_raw_value_to_row(
            self,
            row_index,
            raw_value,
            emit_raw_change=True,
        ):
        state = self._row_state.get(row_index, {})
        normalized = self._normalize_user_raw_value(
            raw_value,
            state.get("bit_length"),
        )
        if normalized is None:
            return False

        state["last_raw"] = normalized
        self._set_raw_item_text(row_index, normalized)
        was_syncing = self._syncing_raw_value
        self._syncing_raw_value = True
        try:
            self._sync_decoded_value_from_raw(row_index, normalized)
        finally:
            self._syncing_raw_value = was_syncing
        if emit_raw_change:
            self._emit_raw_value_changed(row_index, normalized)
        self._update_check_result_if_visible(row_index, normalized)
        return True

    def _handle_item_changed(self, item):
        if self._syncing_raw_value or item.column() != 4:
            return

        row_index = item.row()
        if self._apply_raw_value_to_row(row_index, item.text()):
            return

        state = self._row_state.get(row_index, {})
        previous = state.get("last_raw", "")
        self._set_raw_item_text(row_index, previous)
        QMessageBox.warning(
            self,
            "Invalid Raw Value",
            (
                f"Byte {state.get('byte_pos', row_index)} khong hop le. "
                f"Raw value vuot qua BitLength {state.get('bit_length')}."
            ),
        )

    def _emit_raw_value_changed(self, row_index, raw_value):
        state = self._row_state.get(row_index, {})
        byte_pos = state.get("byte_pos_int")
        bit_pos = state.get("bit_pos")
        bit_length = state.get("bit_length")
        if byte_pos is None or bit_pos is None or bit_length is None:
            return

        self.raw_value_changed.emit(
            row_index,
            byte_pos,
            bit_pos,
            bit_length,
            raw_value,
        )

    def _sync_decoded_value_from_raw(self, row_index, raw_value):
        combo = self.cellWidget(row_index, 5)
        if combo is None:
            return

        for index in range(combo.count()):
            if combo.itemData(index, Qt.UserRole) == raw_value:
                if combo.currentIndex() != index:
                    combo.setCurrentIndex(index)
                return

        if combo.isEditable():
            combo.setEditText(raw_value)
        else:
            combo.setCurrentIndex(-1)

    def _set_raw_item_text(self, row_index, raw_value):
        item = self.item(row_index, 4)
        if item is None or item.text() == raw_value:
            return

        self._syncing_raw_value = True
        item.setText(raw_value)
        self._syncing_raw_value = False

    def _display_raw_value(self, row):
        if row.decoded_options:
            for option in row.decoded_options:
                if option.label == row.decoded_value:
                    return self._format_raw_value(
                        option.raw_value,
                        row.bit_length,
                    )

        return self._format_raw_value(
            row.raw_value,
            row.bit_length,
        )

    @classmethod
    def _normalize_user_raw_value(cls, raw_value, bit_length):
        return normalize_user_raw_value(raw_value, bit_length)

    @classmethod
    def _normalize_raw_tokens(cls, tokens, bit_count):
        return normalize_raw_tokens(tokens, bit_count)

    @classmethod
    def _format_raw_value(cls, raw_value, bit_length):
        return format_raw_value(raw_value, bit_length)

    @staticmethod
    def _format_raw_int(raw_int, bit_count, source_width):
        return format_raw_int(raw_int, bit_count, source_width)

    @classmethod
    def _payload_raw_value(cls, payload_bytes, byte_pos, bit_pos, bit_length):
        return extract_raw_value(payload_bytes, byte_pos, bit_pos, bit_length)

    @staticmethod
    def _parse_payload_bytes(payload):
        return parse_payload_text(payload)

    @staticmethod
    def _hex_tokens(raw_value):
        return hex_tokens(raw_value)

    @staticmethod
    def _is_spaced_hex(raw_value):
        return is_spaced_hex(raw_value)

    @staticmethod
    def _to_int(value):
        return to_int(value)

    def fn_refresh_theme(self):
        super().fn_refresh_theme()

        for row in range(self.rowCount()):
            combo = self.cellWidget(row, 5)
            if hasattr(combo, "fn_refresh_theme"):
                combo.fn_refresh_theme()

            result_item = self.item(row, 8)
            if result_item is not None:
                self._apply_result_style(row, result_item.text())
