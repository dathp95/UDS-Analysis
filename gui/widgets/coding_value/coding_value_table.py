import re

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

    def filter_by_parameter(self, keyword):
        text = str(keyword or "").strip().lower()
        for row_index in range(self.rowCount()):
            item = self.item(row_index, 0)
            parameter = item.text().lower() if item is not None else ""
            self.setRowHidden(
                row_index,
                bool(text) and text not in parameter,
            )

        self.clearSelection()
        self.setCurrentCell(-1, -1)
    def encode_payload(self, payload):
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
            state["original_raw"] = raw_value
            self._sync_decoded_value_from_raw(row_index, raw_value)
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
        combo = PrimaryComboBox(
            minimum_height=30
        )
        has_option_list = bool(row.decoded_options)
        combo.setEditable(not has_option_list)
        combo.setMaximumHeight(32)
        combo.setMinimumWidth(0)
        combo.setMinimumContentsLength(0)
        combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        combo.setMaxVisibleItems(5 if has_option_list else 12)
        combo.view().setTextElideMode(Qt.ElideRight)
        fn_apply_scrollbar_style(combo.view())

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

        combo.currentIndexChanged.connect(
            lambda index, row_index=row_index, combo=combo: (
                self._sync_raw_value_from_combo(
                    row_index,
                    combo,
                    index,
                )
            )
        )

        return combo

    def _sync_raw_value_from_combo(self, row_index, combo, index):
        raw_value = combo.itemData(index, Qt.UserRole)
        if raw_value in (None, ""):
            return

        item = self.item(row_index, 4)
        if item is not None:
            normalized = str(raw_value)
            self._row_state.get(row_index, {})["last_raw"] = normalized
            self._set_raw_item_text(
                row_index,
                normalized,
            )
            self._emit_raw_value_changed(row_index, normalized)
            self._update_check_result_if_visible(row_index, normalized)

    def _handle_item_changed(self, item):
        if self._syncing_raw_value or item.column() != 4:
            return

        row_index = item.row()
        state = self._row_state.get(row_index, {})
        bit_length = state.get("bit_length")
        normalized = self._normalize_user_raw_value(
            item.text(),
            bit_length,
        )

        if normalized is None:
            previous = state.get("last_raw", "")
            self._set_raw_item_text(row_index, previous)
            QMessageBox.warning(
                self,
                "Invalid Raw Value",
                (
                    f"Byte {state.get('byte_pos', row_index)} khong hop le. "
                    f"Raw value vuot qua BitLength {bit_length}."
                ),
            )
            return

        self._set_raw_item_text(row_index, normalized)
        state["last_raw"] = normalized
        self._sync_decoded_value_from_raw(row_index, normalized)
        self._emit_raw_value_changed(row_index, normalized)
        self._update_check_result_if_visible(row_index, normalized)

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
        text = str(raw_value or "").strip()
        if not text:
            return None

        bit_count = cls._to_int(bit_length)
        tokens = cls._hex_tokens(text)
        if not tokens:
            return None

        if cls._is_spaced_hex(text) and bit_count is not None and bit_count <= 4:
            return cls._normalize_raw_tokens(tokens, bit_count)

        hex_text = "".join(tokens)
        raw_int = int(hex_text, 16)
        if bit_count is not None and bit_count > 0:
            max_value = (1 << bit_count) - 1
            if raw_int > max_value:
                return None

        return cls._format_raw_int(raw_int, bit_count, len(hex_text))

    @classmethod
    def _normalize_raw_tokens(cls, tokens, bit_count):
        if bit_count is not None and bit_count > 0:
            max_value = (1 << bit_count) - 1
            for token in tokens:
                if int(token, 16) > max_value:
                    return None

        formatted = [
            f"{int(token, 16):02X}"
            for token in tokens
        ]
        return " ".join(formatted)

    @classmethod
    def _format_raw_value(cls, raw_value, bit_length):
        text = str(raw_value or "").strip()
        if not text:
            return ""

        bit_count = cls._to_int(bit_length)
        tokens = cls._hex_tokens(text)
        if not tokens:
            return text.removeprefix("0x").removeprefix("0X")

        if cls._is_spaced_hex(text):
            normalized = cls._normalize_raw_tokens(tokens, bit_count)
            return normalized if normalized is not None else " ".join(tokens)

        hex_text = "".join(tokens)
        return cls._format_raw_int(
            int(hex_text, 16),
            bit_count,
            len(hex_text),
        )

    @staticmethod
    def _format_raw_int(raw_int, bit_count, source_width):
        if bit_count is not None and bit_count > 0:
            width = max(2, (bit_count + 3) // 4)
        else:
            width = max(2, source_width)

        raw_text = f"{raw_int:0{width}X}"
        if bit_count is not None and bit_count > 4:
            if len(raw_text) % 2:
                raw_text = "0" + raw_text
            return " ".join(
                raw_text[index:index + 2]
                for index in range(0, len(raw_text), 2)
            )

        return raw_text

    @classmethod
    def _payload_raw_value(cls, payload_bytes, byte_pos, bit_pos, bit_length):
        bit_offset = cls._to_int(bit_pos)
        bit_count = cls._to_int(bit_length)
        if (
                bit_offset is None
                or bit_count is None
                or bit_count <= 0
                or byte_pos < 0
                or byte_pos >= len(payload_bytes)
            ):
            return ""

        if bit_offset == 0 and bit_count % 8 == 0:
            byte_count = bit_count // 8
            selected = payload_bytes[byte_pos:byte_pos + byte_count]
            if len(selected) != byte_count:
                return ""
            return " ".join(f"{value:02X}" for value in selected)

        byte_count = (bit_offset + bit_count + 7) // 8
        selected = payload_bytes[byte_pos:byte_pos + byte_count]
        if len(selected) != byte_count:
            return ""

        container = int.from_bytes(
            bytes(selected),
            byteorder="little",
        )
        raw_int = (container >> bit_offset) & ((1 << bit_count) - 1)
        return cls._format_raw_int(
            raw_int,
            bit_count,
            max(1, (bit_count + 3) // 4),
        )

    @staticmethod
    def _parse_payload_bytes(payload):
        return [
            int(token, 16)
            for token in re.findall(r"[0-9A-Fa-f]{2}", payload or "")
        ]

    @staticmethod
    def _hex_tokens(raw_value):
        text = str(raw_value or "").strip()
        text = re.sub(r"(?i)0x", "", text)
        tokens = re.findall(r"[0-9A-Fa-f]+", text)
        if not tokens or "".join(tokens) != re.sub(r"\s+", "", text):
            return []

        return tokens

    @staticmethod
    def _is_spaced_hex(raw_value):
        return bool(re.search(r"\s", str(raw_value or "").strip()))

    @staticmethod
    def _to_int(value):
        if value is None:
            return None

        text = str(value).strip()
        if not text:
            return None

        try:
            return int(text, 0)
        except ValueError:
            pass

        match = re.match(r"^(\d+)(?:\.0+)?(?:\D.*)?$", text)
        if match:
            return int(match.group(1), 10)

        return None

    def fn_refresh_theme(self):
        super().fn_refresh_theme()

        for row in range(self.rowCount()):
            combo = self.cellWidget(row, 5)
            if hasattr(combo, "fn_refresh_theme"):
                combo.fn_refresh_theme()

            result_item = self.item(row, 8)
            if result_item is not None:
                self._apply_result_style(row, result_item.text())











