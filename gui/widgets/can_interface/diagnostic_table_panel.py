from dataclasses import replace
from uuid import uuid4

from PySide6.QtCore import Qt, QSignalBlocker, Signal
from PySide6.QtGui import QColor, QFontDatabase, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QHBoxLayout, QHeaderView, QSizePolicy, QWidget

from gui.themes.theme_manager import ThemeManager
from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style
from gui.widgets.controls.action_button import ActionButton
from gui.widgets.controls.primary_combobox import PrimaryComboBox
from gui.widgets.controls.primary_label import PrimaryLabel
from gui.widgets.diagnostic.diagnostic_sequence_table import DiagnosticSequenceTable
from gui.widgets.can_interface.panel_theme import apply_panel_theme


class _RowButton(ActionButton):
    def __init__(self):
        super().__init__(">", width=32, height=28)
        self.setToolTip("Diagnostic execution not available until transport milestone.")
        self.setAccessibleName("Request this diagnostic step (UI intent only)")

    def fn_refresh_theme(self):
        super().fn_refresh_theme()
        self.setStyleSheet(self.styleSheet() + "QPushButton { padding: 0px; }")


class CanDiagnosticTablePanel(DiagnosticSequenceTable):
    row_selected = Signal(str)
    row_send_requested = Signal(str)
    selected_rows_changed = Signal(tuple)
    save_requested = Signal()
    load_requested = Signal()
    vehicle_changed = Signal(str)

    COL_CHECK, COL_STEP, COL_ECU, COL_REQUEST, COL_SEND, COL_DELAY, COL_REPEAT, COL_EXPECTED, COL_RECEIVE, COL_RESULT, COL_COMMENT = range(11)
    COL_SEQUENCE_NAME = -1  # Definition field remains in the model, not a visible column.
    HEADERS = ("✓", "Step", "ECU", "Payload (HEX)", ">", "Delay (ms)", "Repeat",
               "Expected Response (HEX)", "Receive Message (HEX)", "Results", "Comment")
    OUTCOMES = frozenset(("Pending", "Running", "Passed", "Failed", "Timeout", "Error", "Not Evaluated"))

    def __init__(self, parent=None, vehicle_service=None):
        self.step_ids = []
        self._checked = set()
        self._runtime = {}
        super().__init__(parent, vehicle_service)

    def _setup_ui(self):
        super()._setup_ui()
        layout = self.layout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.removeItem(self.execution_layout)
        self.execution_settings = QWidget()
        self.execution_settings.setLayout(self.execution_layout)
        self.execution_settings.hide()
        self.title = PrimaryLabel("Select a sequence")
        self.title.setTextFormat(Qt.PlainText)
        self.title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.title.setMinimumWidth(60)
        self.notice = PrimaryLabel("")
        self.notice.setTextFormat(Qt.PlainText)
        self.notice.setWordWrap(True)
        self.notice.hide()
        self.btn_delete = ActionButton("Delete", width=62, height=30)
        self.btn_load = ActionButton("Load .diag", width=85, height=30)
        self.btn_settings = ActionButton("Settings", width=72, height=30)
        self.btn_settings.setCheckable(True)
        self.btn_settings.toggled.connect(self.execution_settings.setVisible)
        self.btn_add.setText("Add Row")
        self.btn_export.setText("Save")
        self.btn_run.setText("Run Selected")
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.btn_run.setToolTip("Diagnostic execution not available until transport milestone.")
        self.btn_stop.setToolTip(self.btn_run.toolTip())
        self.btn_stop.hide()
        self.vehicle_selector.setMaximumWidth(210)
        self.vehicle_selector.cmb_vehicle.setMinimumContentsLength(6)
        self.vehicle_selector.cmb_vehicle.setPlaceholderText("Select Vehicle")
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)
        toolbar.addWidget(self.title, 1)
        toolbar.addWidget(self.vehicle_selector)
        for button in (self.btn_add, self.btn_delete, self.btn_load, self.btn_export, self.btn_run, self.btn_settings):
            button.setMinimumSize(button.minimumWidth() if button not in (self.btn_add, self.btn_export) else 66, 30)
            toolbar.addWidget(button)
        layout.insertLayout(0, toolbar)
        layout.insertWidget(1, self.execution_settings)
        layout.addWidget(self.notice)
        self.btn_delete.clicked.connect(self.fn_remove_selected_step)
        self.btn_load.clicked.connect(self.load_requested)
        self.btn_export.clicked.connect(self.save_requested)
        self.table.currentCellChanged.connect(self._selection_changed)
        self._copy_shortcut = QShortcut(QKeySequence.Copy, self.table)
        self._copy_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        self._copy_shortcut.activated.connect(self.copy_current_cell)

    def _configure_columns(self):
        for column, width in enumerate((34, 50, 110, 165, 36, 85, 65, 185, 185, 100, 160)):
            self.table.setColumnWidth(column, width)
            self.table.horizontalHeader().setSectionResizeMode(column, QHeaderView.Interactive)
        self.table.setMinimumHeight(120)

    def fn_load_sequence(self, test_case):
        self.step_ids = [uuid4().hex for _ in test_case.steps] if test_case else []
        self._checked.clear()
        self._runtime.clear()
        super().fn_load_sequence(test_case)
        self.title.setText(test_case.name if test_case else "Select a sequence")
        self.title.setToolTip(self.title.text())
        self.notice.clear()
        self.notice.hide()
        self._selection_changed()

    def mark_saved(self):
        self._is_dirty = False
        self.title.setText(self._test_case.name if self._test_case else "Select a sequence")

    def fn_add_step_after_selected(self):
        self._ensure_test_case()
        self.step_ids.insert(self._selected_insert_index(), uuid4().hex)
        super().fn_add_step_after_selected()

    def _replace_steps(self, steps):
        # The native model requires a per-step sequence_name. It is no longer a
        # visible column, so new rows inherit the document title, not an uneditable blank.
        named = [replace(step, sequence_name=self._test_case.name) if not step.sequence_name else step for step in steps]
        super()._replace_steps(named)

    def fn_remove_selected_step(self):
        removed = set(self._selected_rows())
        ids = [key for index, key in enumerate(self.step_ids) if index not in removed]
        self._checked.intersection_update(ids)
        self._runtime = {key: value for key, value in self._runtime.items() if key in ids}
        self.step_ids = ids
        super().fn_remove_selected_step()
        self.selected_rows_changed.emit(self.checked_step_ids())
        self._selection_changed()

    def _populate_step_row(self, row, step):
        step_id = self.step_ids[row]
        self._set_item(row, self.COL_CHECK, "", editable=False)
        check = self.table.item(row, self.COL_CHECK)
        check.setFlags(check.flags() | Qt.ItemIsUserCheckable)
        check.setCheckState(Qt.Checked if step_id in self._checked else Qt.Unchecked)
        self._set_item(row, self.COL_STEP, step.step, editable=False)
        self._set_ecu_combo(row, step.ecu)
        for column, value in ((self.COL_REQUEST, step.request), (self.COL_DELAY, self._format_optional_int(step.delay_ms)),
                              (self.COL_REPEAT, step.repeat), (self.COL_EXPECTED, step.expected_response),
                              (self.COL_COMMENT, step.comment)):
            self._set_item(row, column, value, editable=True)
        button = _RowButton()
        button.clicked.connect(lambda checked=False, key=step_id: self._request_step(key))
        self.table.setCellWidget(row, self.COL_SEND, button)
        self._render_runtime(row)

    def _set_item(self, row, column, value, editable):
        super()._set_item(row, column, value, editable)
        item = self.table.item(row, column)
        item.setToolTip(str(value))
        if column in (self.COL_REQUEST, self.COL_EXPECTED, self.COL_RECEIVE):
            item.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))

    def _updated_step_from_item(self, step, column, text):
        updated = replace(step, comment=text) if column == self.COL_COMMENT else super()._updated_step_from_item(step, column, text)
        if updated is None:
            self.show_notice("Invalid value; the previous value was retained.")
        return updated

    def _on_item_changed(self, item):
        if self._is_populating:
            return
        if item.column() == self.COL_CHECK and item.row() < len(self.step_ids):
            key = self.step_ids[item.row()]
            if item.checkState() == Qt.Checked:
                self._checked.add(key)
            else:
                self._checked.discard(key)
            self.selected_rows_changed.emit(self.checked_step_ids())
            return
        super()._on_item_changed(item)

    def _mark_dirty(self):
        self._runtime.clear()
        with QSignalBlocker(self.table):
            for row in range(self.table.rowCount()):
                self._render_runtime(row)
        super()._mark_dirty()

    def _request_step(self, key):
        if key in self.step_ids:
            self.show_notice("Diagnostic execution not available until transport milestone.")
            self.row_send_requested.emit(key)

    def show_notice(self, text):
        self.notice.setText(text)
        self.notice.setVisible(bool(text))

    def checked_step_ids(self):
        return tuple(key for key in self.step_ids if key in self._checked)

    def selected_step_id(self):
        row = self.table.currentRow()
        return self.step_ids[row] if 0 <= row < len(self.step_ids) else ""

    def _selection_changed(self, *_):
        self.row_selected.emit(self.selected_step_id())

    def step_for_id(self, key):
        if key not in self.step_ids:
            return None
        return self._test_case.steps[self.step_ids.index(key)]

    def set_step_running(self, key):
        self.set_step_result(key, "", "Running")

    def set_step_result(self, key, received_payload, outcome, detail=""):
        if key not in self.step_ids:
            return False
        payload = self._normalize_hex(received_payload, allow_empty=True)
        if payload is None or outcome not in self.OUTCOMES:
            raise ValueError("Invalid runtime result")
        self._runtime[key] = (payload, outcome, detail)
        with QSignalBlocker(self.table):
            self._render_runtime(self.step_ids.index(key))
        return True

    def _render_runtime(self, row):
        payload, outcome, detail = self._runtime.get(self.step_ids[row], ("—", "—", ""))
        self._set_item(row, self.COL_RECEIVE, payload, editable=False)
        self._set_item(row, self.COL_RESULT, outcome, editable=False)
        self.table.item(row, self.COL_RESULT).setToolTip(detail or outcome)
        colors = ThemeManager.fn_colors()
        color = colors.SUCCESS if outcome == "Passed" else colors.DANGER if outcome in ("Failed", "Error", "Timeout") else colors.WARNING if outcome in ("Pending", "Running") else colors.TEXT
        self.table.item(row, self.COL_RESULT).setForeground(QColor(color))

    def reset_runtime_results(self):
        self._runtime.clear()
        with QSignalBlocker(self.table):
            for row in range(self.table.rowCount()):
                self._render_runtime(row)

    def copy_current_cell(self):
        item = self.table.currentItem()
        if item is not None:
            QApplication.clipboard().setText(item.text())

    def fn_refresh_vehicles(self, selected_vehicle_name=""):
        chosen = selected_vehicle_name or self._current_vehicle_name
        try:
            names = self._vehicle_service.list_vehicles()
        except Exception as error:
            names = []
            self.show_notice(f"Cannot load vehicles: {error}")
        self.vehicle_selector.fn_set_vehicles(names, chosen if chosen in names else "", allow_empty_selection=True)
        self._load_vehicle_by_name(self.vehicle_selector.fn_vehicle())
        self._refresh_ecu_combos()

    def _on_vehicle_changed(self, vehicle_name):
        super()._on_vehicle_changed(vehicle_name)
        if vehicle_name and self._current_vehicle is None:
            self.show_notice(f"Cannot load Vehicle '{vehicle_name}'.")
        self.vehicle_changed.emit(vehicle_name)

    def _set_ecu_combo(self, row, ecu):
        combo = PrimaryComboBox(minimum_height=28)
        candidates = [value for value in self._available_ecus if value.name == ecu]
        valid = len(candidates) == 1
        if not valid:
            combo.addItem(f"⚠ {ecu or 'Select ECU'}", None)
        for value in self._available_ecus:
            combo.addItem(value.name, value)
        combo.setCurrentIndex(combo.findText(ecu) if valid else 0)
        if not self._current_vehicle:
            combo.setToolTip(f"Select Vehicle to resolve ECU '{ecu}'.")
        elif not valid:
            combo.setToolTip(f"ECU '{ecu}' is missing or ambiguous in the selected Vehicle.")
        else:
            combo.setToolTip(ecu)
        key = self.step_ids[row]
        combo.currentIndexChanged.connect(lambda index, target=key, control=combo: self._ecu_changed(target, control))
        fn_apply_scrollbar_style(combo.view())
        self.table.setCellWidget(row, self.COL_ECU, combo)

    def _ecu_changed(self, key, combo):
        value = combo.currentData()
        if value is not None and key in self.step_ids:
            self._on_ecu_changed(self.step_ids.index(key), value.name)

    def fn_refresh_theme(self):
        apply_panel_theme(self, "canDiagnosticTablePanel")
        with QSignalBlocker(self.table):
            super().fn_refresh_theme()
            for widget in (self.title, self.notice, self.btn_delete, self.btn_load, self.btn_settings):
                widget.fn_refresh_theme()
            for row in range(self.table.rowCount()):
                self.table.cellWidget(row, self.COL_SEND).fn_refresh_theme()
                fn_apply_scrollbar_style(self.table.cellWidget(row, self.COL_ECU).view())
                self._render_runtime(row)
