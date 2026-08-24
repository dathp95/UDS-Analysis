from __future__ import annotations

import re
from dataclasses import replace

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.diagnostic_sequence import (
    DiagnosticExecutionSettings,
    DiagnosticStep,
    DiagnosticTestCase,
)
from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style
from gui.widgets.controls.primary_combobox import PrimaryComboBox
from gui.widgets.controls.primary_label import PrimaryLabel
from gui.widgets.controls.primary_lineedit import PrimaryLineEdit
from gui.widgets.controls.primary_table import PrimaryTable


_HEX_BYTE_PATTERN = re.compile(r"^[0-9A-Fa-f]{2}$")


class DiagnosticSequenceTable(QWidget):

    sequence_modified = Signal(object)

    COL_INDEX = 0
    COL_STEP = 1
    COL_SEQUENCE_NAME = 2
    COL_ECU = 3
    COL_REQUEST = 4
    COL_DELAY = 5
    COL_REPEAT = 6
    COL_EXPECTED = 7
    COL_RECEIVE = 8
    COL_RESULT = 9
    COL_COMMENT = 10

    HEADERS = (
        "Index",
        "Step",
        "Test Sequence Name",
        "ECU",
        "Transmit Message",
        "Delay (ms)",
        "Repeat",
        "Expected Message",
        "Receive Message",
        "Result",
        "Comment",
    )

    def __init__(self, parent=None):
        super().__init__(parent)

        self._test_case: DiagnosticTestCase | None = None
        self._is_populating = False
        self._is_dirty = False

        self._setup_ui()
        self._connect_signals()
        self.fn_load_sequence(None)
        self.fn_refresh_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.settings_layout = QHBoxLayout()
        self.settings_layout.setContentsMargins(0, 0, 0, 0)
        self.settings_layout.setSpacing(8)

        self.lbl_loop = PrimaryLabel("Loop")
        self.txt_loop = PrimaryLineEdit()
        self.txt_loop.setValidator(QIntValidator(1, 9999, self))
        self.txt_loop.setFixedWidth(72)
        self.txt_loop.setText("1")

        self.lbl_command_delay = PrimaryLabel("Command Delay")
        self.txt_command_delay = PrimaryLineEdit()
        self.txt_command_delay.setValidator(QIntValidator(0, 60000, self))
        self.txt_command_delay.setFixedWidth(92)
        self.txt_command_delay.setText("100")
        self.lbl_ms = PrimaryLabel("ms")

        self.lbl_duration = PrimaryLabel("Duration: --")

        self.settings_layout.addWidget(self.lbl_loop)
        self.settings_layout.addWidget(self.txt_loop)
        self.settings_layout.addSpacing(12)
        self.settings_layout.addWidget(self.lbl_command_delay)
        self.settings_layout.addWidget(self.txt_command_delay)
        self.settings_layout.addWidget(self.lbl_ms)
        self.settings_layout.addSpacing(12)
        self.settings_layout.addWidget(self.lbl_duration)
        self.settings_layout.addStretch(1)

        self.table = PrimaryTable()
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSortingEnabled(False)
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked
            | QAbstractItemView.EditKeyPressed
            | QAbstractItemView.AnyKeyPressed
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self._configure_columns()

        layout.addLayout(self.settings_layout)
        layout.addWidget(self.table, 1)

    def _connect_signals(self):
        self.txt_loop.editingFinished.connect(self._on_loop_changed)
        self.txt_command_delay.editingFinished.connect(
            self._on_command_delay_changed
        )
        self.table.itemChanged.connect(self._on_item_changed)

    def fn_load_sequence(self, test_case):
        self._is_populating = True
        self._test_case = test_case
        self._is_dirty = False
        self.table.clearContents()
        self.table.setRowCount(0)

        if test_case is None:
            self.txt_loop.setText("1")
            self.txt_command_delay.setText("100")
            self.lbl_duration.setText("Duration: --")
            self._is_populating = False
            return

        self.txt_loop.setText(str(test_case.execution.loop))
        self.txt_command_delay.setText(
            str(test_case.execution.command_delay_ms)
        )
        self.lbl_duration.setText("Duration: --")

        self.table.setRowCount(len(test_case.steps))
        for row, step in enumerate(test_case.steps):
            self._populate_step_row(row, step)

        self._is_populating = False

    def fn_current_sequence(self):
        return self._test_case

    def fn_is_dirty(self):
        return self._is_dirty

    def fn_add_step(self):
        if self._test_case is None:
            self._test_case = DiagnosticTestCase(
                schema_version=1,
                name="Untitled Diagnostic Sequence",
                description="",
                enabled=True,
                execution=DiagnosticExecutionSettings(),
                steps=[],
            )

        next_index = len(self._test_case.steps) + 1
        step = DiagnosticStep(
            step=next_index,
            sequence_name=self._test_case.name,
            ecu="",
            request="",
            delay_ms=None,
            repeat=1,
        )
        steps = [*self._test_case.steps, step]
        self._replace_test_case(steps=steps)
        self._is_populating = True
        self.table.setRowCount(next_index)
        self._populate_step_row(next_index - 1, step)
        self._is_populating = False
        self._mark_dirty()

    def fn_remove_selected_step(self):
        return None

    def fn_move_step_up(self):
        return None

    def fn_move_step_down(self):
        return None

    def _populate_step_row(self, row, step):
        self._set_item(row, self.COL_INDEX, row + 1, editable=False)
        self._set_item(row, self.COL_STEP, step.step, editable=True)
        self._set_item(row, self.COL_SEQUENCE_NAME, step.sequence_name, editable=True)
        self._set_ecu_combo(row, step.ecu)
        self._set_item(row, self.COL_REQUEST, step.request, editable=True)
        self._set_item(row, self.COL_DELAY, self._format_optional_int(step.delay_ms), editable=True)
        self._set_item(row, self.COL_REPEAT, step.repeat, editable=True)
        self._set_item(row, self.COL_EXPECTED, step.expected_response, editable=True)
        self._set_item(row, self.COL_RECEIVE, "", editable=False)
        self._set_item(row, self.COL_RESULT, "", editable=False)
        self._set_item(row, self.COL_COMMENT, step.comment, editable=True)

    def _set_item(self, row, column, value, editable):
        alignment = Qt.AlignCenter if column in (
            self.COL_INDEX,
            self.COL_STEP,
            self.COL_DELAY,
            self.COL_REPEAT,
            self.COL_RESULT,
        ) else Qt.AlignLeft | Qt.AlignVCenter
        item = self.table.fn_create_item(value, row, alignment=alignment)
        if not editable:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, column, item)

    def _set_ecu_combo(self, row, ecu):
        combo = PrimaryComboBox(minimum_height=28)
        values = [ecu] if ecu else [""]
        combo.addItems(values)
        combo.setCurrentText(ecu)
        combo.currentTextChanged.connect(
            lambda value, current_row=row: self._on_ecu_changed(current_row, value)
        )
        combo.fn_refresh_theme()
        fn_apply_scrollbar_style(combo.view())
        self.table.setCellWidget(row, self.COL_ECU, combo)

    def _on_loop_changed(self):
        value = self._validated_int(
            self.txt_loop.text(),
            minimum=1,
            maximum=9999,
        )
        if value is None:
            self._restore_execution_inputs()
            return
        if self._test_case is None or self._test_case.execution.loop == value:
            return

        execution = replace(self._test_case.execution, loop=value)
        self._replace_test_case(execution=execution)
        self._mark_dirty()

    def _on_command_delay_changed(self):
        value = self._validated_int(
            self.txt_command_delay.text(),
            minimum=0,
            maximum=60000,
        )
        if value is None:
            self._restore_execution_inputs()
            return
        if (
            self._test_case is None
            or self._test_case.execution.command_delay_ms == value
        ):
            return

        execution = replace(
            self._test_case.execution,
            command_delay_ms=value,
        )
        self._replace_test_case(execution=execution)
        self._mark_dirty()

    def _on_item_changed(self, item):
        if self._is_populating or self._test_case is None:
            return

        row = item.row()
        column = item.column()
        if row >= len(self._test_case.steps):
            return

        step = self._test_case.steps[row]
        updated_step = self._updated_step_from_item(step, column, item.text())
        if updated_step is None:
            self._restore_step_row(row, step)
            return
        if updated_step == step:
            return

        steps = list(self._test_case.steps)
        steps[row] = updated_step
        self._replace_test_case(steps=steps)
        self._restore_step_row(row, updated_step)
        self._mark_dirty()

    def _on_ecu_changed(self, row, value):
        if self._is_populating or self._test_case is None:
            return
        if row >= len(self._test_case.steps):
            return

        step = self._test_case.steps[row]
        if step.ecu == value:
            return
        steps = list(self._test_case.steps)
        steps[row] = replace(step, ecu=value)
        self._replace_test_case(steps=steps)
        self._mark_dirty()

    def _updated_step_from_item(self, step, column, text):
        if column == self.COL_STEP:
            value = self._validated_int(text, minimum=1)
            return replace(step, step=value) if value is not None else None
        if column == self.COL_SEQUENCE_NAME:
            return replace(step, sequence_name=text.strip())
        if column == self.COL_REQUEST:
            value = self._normalize_hex(text, allow_empty=True)
            return replace(step, request=value) if value is not None else None
        if column == self.COL_DELAY:
            value = self._validated_optional_int(text, minimum=0)
            return replace(step, delay_ms=value) if value is not False else None
        if column == self.COL_REPEAT:
            value = self._validated_int(text, minimum=1)
            return replace(step, repeat=value) if value is not None else None
        if column == self.COL_EXPECTED:
            value = self._normalize_hex(text, allow_empty=True)
            return replace(step, expected_response=value) if value is not None else None
        if column == self.COL_COMMENT:
            return replace(step, comment=text.strip())
        return step

    def _restore_execution_inputs(self):
        self._is_populating = True
        if self._test_case is None:
            self.txt_loop.setText("1")
            self.txt_command_delay.setText("100")
        else:
            self.txt_loop.setText(str(self._test_case.execution.loop))
            self.txt_command_delay.setText(
                str(self._test_case.execution.command_delay_ms)
            )
        self._is_populating = False

    def _restore_step_row(self, row, step):
        self._is_populating = True
        self._populate_step_row(row, step)
        self._is_populating = False

    def _replace_test_case(self, **changes):
        if self._test_case is not None:
            self._test_case = replace(self._test_case, **changes)

    def _mark_dirty(self):
        self._is_dirty = True
        self.sequence_modified.emit(self._test_case)

    @staticmethod
    def _format_optional_int(value):
        return "" if value is None else str(value)

    @staticmethod
    def _validated_int(text, minimum=None, maximum=None):
        try:
            value = int(str(text).strip())
        except (TypeError, ValueError):
            return None
        if minimum is not None and value < minimum:
            return None
        if maximum is not None and value > maximum:
            return None
        return value

    @staticmethod
    def _validated_optional_int(text, minimum=None):
        text = str(text).strip()
        if text == "":
            return None
        value = DiagnosticSequenceTable._validated_int(text, minimum=minimum)
        if value is None:
            return False
        return value

    @staticmethod
    def _normalize_hex(text, allow_empty=False):
        text = str(text).strip()
        if not text:
            return "" if allow_empty else None
        tokens = text.split()
        if any(not _HEX_BYTE_PATTERN.fullmatch(token) for token in tokens):
            return None
        return " ".join(token.upper() for token in tokens)

    def _configure_columns(self):
        widths = {
            self.COL_INDEX: 56,
            self.COL_STEP: 56,
            self.COL_SEQUENCE_NAME: 180,
            self.COL_ECU: 110,
            self.COL_REQUEST: 150,
            self.COL_DELAY: 88,
            self.COL_REPEAT: 72,
            self.COL_EXPECTED: 160,
            self.COL_RECEIVE: 150,
            self.COL_RESULT: 90,
            self.COL_COMMENT: 180,
        }
        header = self.table.horizontalHeader()
        for column, width in widths.items():
            self.table.setColumnWidth(column, width)
            header.setSectionResizeMode(column, QHeaderView.Interactive)
        header.setSectionResizeMode(self.COL_COMMENT, QHeaderView.Stretch)
        self.table.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

    def fn_refresh_theme(self):
        for label in (
            self.lbl_loop,
            self.lbl_command_delay,
            self.lbl_ms,
            self.lbl_duration,
        ):
            label.fn_refresh_theme()
        self.txt_loop.fn_refresh_theme()
        self.txt_command_delay.fn_refresh_theme()
        self.table.fn_refresh_theme()
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, self.COL_ECU)
            if hasattr(combo, "fn_refresh_theme"):
                combo.fn_refresh_theme()
