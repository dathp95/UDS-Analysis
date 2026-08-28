from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.themes.theme_manager import ThemeManager
from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style
from gui.widgets.controls.primary_checkbox import PrimaryCheckBox
from gui.widgets.controls.primary_label import PrimaryLabel
from repositories.diagnostic_sequence_repository import (
    DiagnosticSequenceRepository,
    DiagnosticSequenceValidationError,
)


class DiagnosticSequenceList(QWidget):

    sequence_selected = Signal(object)
    selection_changed = Signal(list)

    ITEM_PATH_ROLE = Qt.UserRole
    ITEM_MODEL_ROLE = Qt.UserRole + 1

    def __init__(self, repository=None, parent=None):
        super().__init__(parent)

        self._repository = repository or DiagnosticSequenceRepository()
        self._is_updating = False

        self._setup_ui()
        self._connect_signals()
        self.fn_refresh_sequences()
        self.fn_refresh_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.chk_select_all = PrimaryCheckBox("Select All")
        self._update_select_all_text(False)
        self.list_sequences = QListWidget()
        self.list_sequences.setSelectionMode(QListWidget.SingleSelection)
        self.list_sequences.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.list_sequences.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lbl_empty = PrimaryLabel("No diagnostic sequences found.")
        self.lbl_error = PrimaryLabel("")
        self.lbl_error.setWordWrap(True)

        layout.addWidget(self.chk_select_all)
        layout.addWidget(self.list_sequences, 1)
        layout.addWidget(self.lbl_empty)
        layout.addWidget(self.lbl_error)

    def _connect_signals(self):
        self.chk_select_all.toggled.connect(
            self._on_select_all_toggled
        )
        self.list_sequences.itemChanged.connect(
            self._on_item_changed
        )
        self.list_sequences.itemClicked.connect(
            self._on_item_clicked
        )

    def fn_refresh_sequences(self):
        selected_paths = set(self._selected_paths())
        self._is_updating = True
        self.list_sequences.clear()
        errors = []

        try:
            sequence_paths = self._sorted_sequence_paths(
                self._repository.fn_list_sequences()
            )
        except Exception as error:
            sequence_paths = []
            errors.append(str(error))

        for path in sequence_paths:
            try:
                test_case = self._repository.fn_load_sequence(path)
            except DiagnosticSequenceValidationError as error:
                errors.append(f"{Path(path).name}: {error}")
                continue

            item = self._create_sequence_item(
                path,
                test_case,
            )
            if str(path) in selected_paths:
                item.setCheckState(Qt.Checked)
            self.list_sequences.addItem(item)

        self._is_updating = False
        self._refresh_empty_state()
        self._set_errors(errors)
        self._sync_select_all_state()
        self._emit_selection_changed()

    def fn_selected_sequences(self):
        selected = []
        for index in range(self.list_sequences.count()):
            item = self.list_sequences.item(index)
            if item.checkState() == Qt.Checked:
                selected.append(
                    item.data(self.ITEM_MODEL_ROLE)
                )

        return selected

    def fn_clear_selection(self):
        self._is_updating = True
        for index in range(self.list_sequences.count()):
            self.list_sequences.item(index).setCheckState(Qt.Unchecked)
        self.chk_select_all.setChecked(False)
        self._update_select_all_text(False)
        self._is_updating = False
        self._emit_selection_changed()

    def _create_sequence_item(self, path, test_case):
        item = QListWidgetItem(
            self._display_name(path, test_case)
        )
        item.setFlags(
            item.flags()
            | Qt.ItemIsUserCheckable
            | Qt.ItemIsEnabled
            | Qt.ItemIsSelectable
        )
        item.setCheckState(Qt.Unchecked)
        item.setData(self.ITEM_PATH_ROLE, str(path))
        item.setData(self.ITEM_MODEL_ROLE, test_case)
        return item

    def _on_select_all_toggled(self, checked):
        if self._is_updating:
            return

        self._update_select_all_text(checked)
        self._is_updating = True
        state = Qt.Checked if checked else Qt.Unchecked
        for index in range(self.list_sequences.count()):
            self.list_sequences.item(index).setCheckState(state)
        self._is_updating = False
        self._emit_selection_changed()

    def _on_item_changed(self, _item):
        if self._is_updating:
            return

        self._sync_select_all_state()
        self._emit_selection_changed()

    def _on_item_clicked(self, item):
        test_case = item.data(self.ITEM_MODEL_ROLE)
        if test_case is not None:
            self.sequence_selected.emit(test_case)

    def _sync_select_all_state(self):
        self._is_updating = True
        count = self.list_sequences.count()
        all_checked = (
            count > 0
            and all(
                self.list_sequences.item(index).checkState() == Qt.Checked
                for index in range(count)
            )
        )
        self.chk_select_all.setChecked(all_checked)
        self._update_select_all_text(all_checked)
        self._is_updating = False

    def _update_select_all_text(self, checked):
        text = "✓ Select All" if checked else "Select All"
        self.chk_select_all.setText(text)

    def _emit_selection_changed(self):
        self.selection_changed.emit(
            self.fn_selected_sequences()
        )

    def _selected_paths(self):
        selected = []
        for index in range(self.list_sequences.count()):
            item = self.list_sequences.item(index)
            if item.checkState() == Qt.Checked:
                selected.append(
                    item.data(self.ITEM_PATH_ROLE)
                )
        return selected

    def _refresh_empty_state(self):
        has_sequences = self.list_sequences.count() > 0
        self.lbl_empty.setVisible(not has_sequences)
        self.chk_select_all.setEnabled(has_sequences)

    def _set_errors(self, errors):
        self.lbl_error.setText("\n".join(errors))
        self.lbl_error.setVisible(bool(errors))

    @staticmethod
    def _sorted_sequence_paths(paths):
        return sorted(
            paths,
            key=DiagnosticSequenceList._sequence_sort_key,
        )

    @staticmethod
    def _sequence_sort_key(path):
        stem = Path(path).stem
        match = re.match(r"^(\d+)", stem)
        if match:
            return (
                0,
                int(match.group(1)),
                stem.lower(),
            )
        return (
            1,
            stem.lower(),
        )

    @staticmethod
    def _display_name(path, test_case):
        prefix = DiagnosticSequenceList._display_prefix(path)
        if prefix:
            return f"{prefix}. {test_case.name}"
        return test_case.name

    @staticmethod
    def _display_prefix(path):
        match = re.match(
            r"^(\d+)",
            Path(path).stem,
        )
        if not match:
            return ""
        return match.group(1)

    def fn_refresh_theme(self):
        colors = ThemeManager.fn_colors()

        self.chk_select_all.fn_refresh_theme()
        self.lbl_empty.fn_refresh_theme()
        self.lbl_error.fn_refresh_theme()
        self.list_sequences.setStyleSheet(
            f"""
            QListWidget {{
                background: {colors.WINDOW};
                color: {colors.TEXT};
                border: 1px solid {colors.BORDER};
                border-radius: 6px;
                padding: 4px;
            }}
            QListWidget::item {{
                min-height: 28px;
                padding: 4px;
            }}
            QListWidget::item:selected {{
                background: {colors.PRIMARY};
                color: {colors.TEXT_INVERT};
            }}
            """
        )
        self.lbl_error.setStyleSheet(
            f"""
            QLabel {{
                color: {colors.WARNING};
            }}
            """
        )
        fn_apply_scrollbar_style(self.list_sequences)
