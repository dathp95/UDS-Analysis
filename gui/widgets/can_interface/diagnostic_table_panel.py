import re

from dataclasses import replace
from uuid import uuid4
from core.diagnostic_request import SECURITY_SEED_REQUESTS
from html import escape

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
from services.can.diag_ecu_mapper import find_ecu_by_can_ids

class _RowButton(ActionButton):
    def __init__(self):
        super().__init__(">", width=32, height=28)
        self.setToolTip("Send one manual UDS request on the connected channel.")
        self.setAccessibleName("Send this one diagnostic step")

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
    document_changed=Signal()
    vehicle_configuration_changed=Signal()
    vehicle_resources_changed=Signal()

    COL_CHECK, COL_STEP, COL_SEQUENCE_NAME, COL_ECU, COL_REQUEST, COL_SEND, COL_DELAY, COL_REPEAT, COL_EXPECTED, COL_RECEIVE, COL_RESULT, COL_COMMENT = range(12)
    HEADERS = ("✓", "Step", "Test sequence name", "ECU", "Payload (HEX)", ">", "Delay (ms)", "Repeat",
               "Expected Response (HEX)", "Receive Message (HEX)", "Results", "Comment")
    OUTCOMES = frozenset(("Pending", "Running", "Passed", "Failed", "Timeout", "Error", "Not Evaluated", "Cancelled"))

    def __init__(self, parent=None, vehicle_service=None):
        self.step_ids = []
        self._checked = set()
        self._runtime = {}
        self._auto_comments = {}
        self._step_signatures = {}
        self._request_busy=False
        self._send_available=True  # Standalone view can still emit typed action intent.
        self.import_diagnostics = ()
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
        self.notice.setMaximumHeight(40)
        self.notice.hide()
        self.btn_delete = ActionButton("Delete", width=62, height=30)
        self.btn_load = ActionButton("Load .diag", width=85, height=30)
        self.btn_load.hide()
        self.btn_settings = ActionButton("Settings", width=72, height=30)
        self.btn_settings.setCheckable(True)
        self.btn_settings.toggled.connect(self.execution_settings.setVisible)
        self.btn_add.setText("Add Row")
        self.btn_export.setText("Save")
        self.btn_export.hide()  # Compatibility signal remains; visible Save belongs to sidebar.
        self.btn_run.setText("Run Selected")
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.btn_run.setToolTip("Automatic sequence execution is not enabled in M04.")
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
        for column, width in enumerate((34, 50, 160, 110, 165, 36, 85, 65, 185, 185, 100, 160)):
            self.table.setColumnWidth(column, width)
            self.table.horizontalHeader().setSectionResizeMode(column, QHeaderView.Interactive)
        self.table.setMinimumHeight(120)

    def fn_load_sequence(self, test_case):
        self._auto_comments.clear()
        self.step_ids = [uuid4().hex for _ in test_case.steps] if test_case else []
        self._checked.clear()
        self._runtime.clear()
        self.import_diagnostics = ()
        super().fn_load_sequence(test_case)
        self._step_signatures = self._runtime_signatures()
        self.title.setText(test_case.name if test_case else "Select a sequence")
        self.title.setToolTip(self.title.text())
        self.notice.clear()
        self.notice.hide()
        self._selection_changed()
        self.document_changed.emit()

    def mark_saved(self):
        self._is_dirty = False
        self.title.setText(self._test_case.name if self._test_case else "Select a sequence")

    def fn_add_step_after_selected(self):
        self._ensure_test_case()
        self.step_ids.insert(self._selected_insert_index(), uuid4().hex)
        super().fn_add_step_after_selected()

    def _replace_steps(self, steps):
        # Preserve user-entered values, including empty names.
        super()._replace_steps(steps)

    def fn_remove_selected_step(self):
        removed = set(self._selected_rows())
        ids = [key for index, key in enumerate(self.step_ids) if index not in removed]
        self._checked.intersection_update(ids)
        self._runtime = {key: value for key, value in self._runtime.items() if key in ids}
        self._auto_comments = {key: value for key, value in self._auto_comments.items() if key in ids}
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
        self._set_item(row, self.COL_SEQUENCE_NAME, step.sequence_name, editable=True)
        self._set_ecu_combo(row, step.ecu)
        for column, value in ((self.COL_REQUEST, step.request), (self.COL_DELAY, self._format_optional_int(step.delay_ms)),
                              (self.COL_REPEAT, step.repeat), (self.COL_EXPECTED, step.expected_response),
                              (self.COL_COMMENT, step.comment)):
            self._set_item(row, column, value, editable=True)
        button = _RowButton()
        button.clicked.connect(lambda checked=False, key=step_id: self._request_step(key))
        self.table.setCellWidget(row, self.COL_SEND, button)
        self._set_button_state(row)
        self._render_runtime(row)

    def _set_item(self, row, column, value, editable):
        super()._set_item(row, column, value, editable)
        item = self.table.item(row, column)
        item.setToolTip(escape(str(value)))
        if column in (self.COL_REQUEST, self.COL_EXPECTED, self.COL_RECEIVE):
            item.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))

    def _updated_step_from_item(self, step, column, text):

        if column == self.COL_SEQUENCE_NAME:
            return replace(
                step,
                sequence_name=text
            )

        if column == self.COL_COMMENT:
            return replace(step, comment=text)

        # Allow incomplete HEX drafts.
        if column == self.COL_REQUEST:
            return replace(step, request=text)

        if column == self.COL_EXPECTED:
            return replace(step, expected_response=text)

        return super()._updated_step_from_item(
            step, column, text
        )

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
        current = self._runtime_signatures()
        for key in self._step_signatures.keys() | current.keys():
            if self._step_signatures.get(key) != current.get(key):
                self.invalidate_step_result(key)
        self._step_signatures = current
        super()._mark_dirty()

    def _runtime_signatures(self):
        return {key: (step.ecu, step.request, step.expected_response, step.match)
                for key, step in zip(self.step_ids, self._test_case.steps if self._test_case else ())}

    def invalidate_step_result(self, key):
        self._auto_comments.pop(key, None)
        self._runtime.pop(key, None)
        if key in self.step_ids:
            row = self.step_ids.index(key)
            with QSignalBlocker(self.table):
                self._render_runtime(row)
                self._set_button_state(row)

    def _request_step(self, key):
        if key in self.step_ids:
            row=self.step_ids.index(key)
            step=self._test_case.steps[row]
            payload = self._request_payload(step.request)
            if payload is None:
                self.show_notice('Invalid or empty HEX payload.');return
            if payload[0] == 0x27 and payload not in SECURITY_SEED_REQUESTS:
                self.show_notice('Security Access permits only exact 27 01 requestSeed; key submission is not enabled.');return
            if not self._resolved_ecu(step.ecu):
                self.show_notice('Select Vehicle and a configured ECU before sending.');return
            if not self._request_busy and self._send_available: self.row_send_requested.emit(key)

    def set_request_busy(self,busy):
        self._request_busy=bool(busy)
        for row in range(self.table.rowCount()): self._set_button_state(row)

    def set_send_available(self,available):
        self._send_available=bool(available)
        for row in range(self.table.rowCount()): self._set_button_state(row)

    def _set_button_state(self, row):
        button = self.table.cellWidget(row, self.COL_SEND)

        if button is None:
            return

        step = self._test_case.steps[row]

        payload = self._request_payload(step.request)
        payload_valid = payload is not None

        security = (
            payload_valid
            and payload[0] == 0x27 and payload not in SECURITY_SEED_REQUESTS
        )

        target_valid = self._resolved_ecu(step.ecu)

        enabled = (
            self._send_available
            and not self._request_busy
            and not security
            and target_valid
            and payload_valid
        )

        button.setEnabled(enabled)

        if not payload_valid:
            tooltip = "Invalid or empty HEX payload."
        elif security:
            tooltip = "Only exact 27 01 requestSeed is enabled; key submission is disabled."
        elif not target_valid:
            tooltip = "Select a configured ECU."
        elif self._request_busy:
            tooltip = "A diagnostic request is running."
        elif not self._send_available:
            tooltip = "Connect Vector first."
        elif payload in SECURITY_SEED_REQUESTS:
            tooltip = ("Auto SecurityAccess L1: two UDS transactions; final ECU 67 02 required."
                       if self._request_payload(step.expected_response) == b'\x67\x02' else
                       "Request seed manually with 27 01; no key submission or ECU unlock.")
        else:
            tooltip = "Send one manual UDS request."

        button.setToolTip(tooltip)

    def show_notice(self, text):
        self.notice.setText(text)
        self.notice.setToolTip(escape(text))
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

    def set_auto_step_result(self, key, received_payload, outcome, detail):
        """Runtime-only annotation; never mutate the editable sequence model."""
        self._auto_comments[key] = detail
        return self.set_step_result(key, received_payload, outcome, detail)

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
        step = self._test_case.steps[row]
        annotation = self._auto_comments.get(self.step_ids[row])
        if annotation is not None:
            comment = ' | '.join(value for value in (step.comment, annotation) if value)
            self._set_item(row, self.COL_COMMENT, comment, editable=False)
        else:
            self._set_item(row, self.COL_COMMENT, step.comment, editable=True)
        colors = ThemeManager.fn_colors()
        color = colors.SUCCESS if outcome == "Passed" else colors.DANGER if outcome in ("Failed", "Error", "Timeout") else colors.WARNING if outcome in ("Pending", "Running") else colors.TEXT
        self.table.item(row, self.COL_RESULT).setForeground(QColor(color))

    def reset_runtime_results(self):
        self._auto_comments.clear()
        self._runtime.clear()
        with QSignalBlocker(self.table):
            for row in range(self.table.rowCount()):
                self._render_runtime(row)

    def copy_current_cell(self):
        item = self.table.currentItem()
        if item is not None:
            QApplication.clipboard().setText(item.text())

    def _transport_configuration(self):
        if self._current_vehicle is None:
            return None
        return (self._current_vehicle_name, tuple(sorted(
            (ecu.name, ecu.request_id, ecu.response_id) for ecu in self._available_ecus)))

    def fn_refresh_vehicles(self, selected_vehicle_name="", *, preserve_unchanged=False):
        previous = self._transport_configuration()
        chosen = selected_vehicle_name or self._current_vehicle_name
        try:
            names = self._vehicle_service.list_vehicles()
        except Exception as error:
            names = []
            self.show_notice(f"Cannot load vehicles: {error}")
        self.vehicle_selector.fn_set_vehicles(names, chosen if chosen in names else "", allow_empty_selection=True)
        self._load_vehicle_by_name(self.vehicle_selector.fn_vehicle())
        self._apply_diag_ecu_mapping()
        self._refresh_ecu_combos()
        if preserve_unchanged and previous is not None and previous == self._transport_configuration():
            self.vehicle_resources_changed.emit()
        else:
            self.reset_runtime_results()
            self.vehicle_configuration_changed.emit()

    def _on_vehicle_changed(self, vehicle_name):
        self.reset_runtime_results()

        # Load newly selected Vehicle and its ECU definitions.
        super()._on_vehicle_changed(vehicle_name)

        # Map imported .diag addressing to V-CODE ECU names.
        self._apply_diag_ecu_mapping()

        if vehicle_name and self._current_vehicle is None:
            self.show_notice(
                f"Cannot load Vehicle '{vehicle_name}'."
            )

        self.vehicle_changed.emit(vehicle_name)
        self.vehicle_configuration_changed.emit()

    def fn_set_vehicle(self, vehicle):
        self.reset_runtime_results()
        super().fn_set_vehicle(vehicle)
        self._apply_diag_ecu_mapping()
        self.vehicle_configuration_changed.emit()

    
    def _set_ecu_combo(self, row, ecu):
        combo = PrimaryComboBox(minimum_height=28)

        # Populate only valid, uniquely named ECU definitions.
        valid_ecus = [
            item
            for item in self._available_ecus
            if self._resolved_ecu(item.name)
        ]

        for item in valid_ecus:
            combo.addItem(item.name, item)

        # No empty item at index 0.
        # -1 means no ECU has been selected.
        selected_index = combo.findText(ecu) if ecu else -1

        if selected_index >= 0:
            combo.setCurrentIndex(selected_index)
        else:
            combo.setCurrentIndex(-1)

        # Show empty editor text when no ECU is selected,
        # without creating a selectable blank option.
        combo.setPlaceholderText("")

        if self._current_vehicle is None:
            tooltip = "Select a Vehicle first."
        elif not ecu:
            tooltip = "Select an ECU."
        elif selected_index < 0:
            tooltip = (
                f"ECU '{ecu}' is not configured "
                "in the selected Vehicle."
            )
        else:
            tooltip = ecu

        combo.setToolTip(escape(tooltip))

        key = self.step_ids[row]

        combo.currentIndexChanged.connect(
            lambda index, target=key, control=combo:
                self._ecu_changed(target, control)
        )

        fn_apply_scrollbar_style(combo.view())

        self.table.setCellWidget(
            row,
            self.COL_ECU,
            combo,
        )


    def _resolved_ecu(self, name):
        return bool(name and name.strip() and self._current_vehicle is not None
                    and sum(ecu.name == name for ecu in self._available_ecus) == 1)

    def unresolved_ecus(self):
        if self._current_vehicle is None or self._test_case is None:
            return ()
        return tuple((row + 1, step.ecu) for row, step in enumerate(self._test_case.steps)
                     if not self._resolved_ecu(step.ecu))

    def _refresh_ecu_combos(self):
        super()._refresh_ecu_combos()

        for row in range(self.table.rowCount()):
            self._set_button_state(row)

        # Empty ECU is a valid draft state.
        # Only show a warning for nonempty unresolved ECU names.
        unknown = tuple(
            (row, name)
            for row, name in self.unresolved_ecus()
            if str(name or "").strip()
        )

        if unknown:
            details = "\n".join(
                f"Row {row}: {name}"
                for row, name in unknown
            )

            self.show_notice(
                f"{len(unknown)} unresolved ECU(s)."
            )
            self.notice.setToolTip(details)
        else:
            # Clear only an ECU warning previously set by this method.
            if self.notice.text().endswith("unresolved ECU(s)."):
                self.show_notice("")

    def sequence_for_save(self):
        """
        Save editor content as-is.

        Empty ECU, incomplete HEX and empty sequence names
        are allowed in saved drafts.

        ECU resolution and HEX validation are required
        before sending diagnostic requests.
        """
        return self._test_case
    
    def exchange_text(self):
        from core.sequence_exchange import export_sequence_text
        case = self.sequence_for_save()
        return export_sequence_text(case.steps if case else (),
                                    [self._runtime.get(key, ('', '', ''))[1] for key in self.step_ids])

    def apply_import(self, imported, mode):
        if mode not in ('append', 'replace') or self._test_case is None:
            raise ValueError('Select an active document and explicit Append or Replace mode.')
        if mode == 'replace':
            self.fn_load_sequence(replace(self._test_case, steps=list(imported.steps)))
        else:
            self.step_ids.extend(uuid4().hex for _ in imported.steps)
            self._replace_steps([*self._test_case.steps, *imported.steps])
            self._reload_steps_into_table()
        self.import_diagnostics = imported.diagnostics
        self._mark_dirty()
        self._refresh_ecu_combos()
        if imported.diagnostics:
            self.show_notice('\n'.join(imported.diagnostics))

    def _ecu_changed(self, key, combo):
        value = combo.currentData()
        if key not in self.step_ids or self._is_populating:
            return
        row = self.step_ids.index(key)
        name = value.name if value is not None else ''
        step = self._test_case.steps[row]
        if step.ecu != name:
            steps = list(self._test_case.steps)
            steps[row] = replace(step, ecu=name)
            self._replace_steps(steps)
            self._mark_dirty()
   
    def _apply_diag_ecu_mapping(self):
        """
        Remap steps imported from .diag using the
        currently selected Vehicle.

        Do not alter steps without original CAN IDs.
        """
        if self._test_case is None:
            return False

        changed = False
        steps = list(self._test_case.steps)

        for index, step in enumerate(steps):

            # Native manually created steps remain untouched.
            if (
                step.source_request_id is None
                or step.source_response_id is None
            ):
                continue

            mapped_name = find_ecu_by_can_ids(
                self._current_vehicle,
                step.source_request_id,
                step.source_response_id,
            )

            # No match or ambiguous match -> empty ECU.
            if step.ecu != mapped_name:
                steps[index] = replace(
                    step,
                    ecu=mapped_name,
                )
                changed = True

        if not changed:
            return False

        # Update the document model.
        self._replace_steps(steps)

        # Update ECU comboboxes without triggering user edits.
        self._refresh_ecu_combos()

        # Update unsaved RAM draft and the "*" indicator.
        self._mark_dirty()

        return True
   
   
    @staticmethod
    def _is_valid_request_hex(value):
        text = str(value or "").strip()

        if not text:
            return False

        tokens = text.split()

        return all(
            re.fullmatch(r"[0-9A-Fa-f]{2}", token)
            for token in tokens
        )

    @classmethod
    def _request_payload(cls, value):
        if not cls._is_valid_request_hex(value):
            return None
        return bytes.fromhex(' '.join(str(value).split()))

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
