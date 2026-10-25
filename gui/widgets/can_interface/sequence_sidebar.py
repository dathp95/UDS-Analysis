from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QAbstractItemView, QListWidget, QStyle, QStyleOptionViewItem

from gui.widgets.diagnostic.diagnostic_sequence_list import DiagnosticSequenceList
from gui.widgets.controls.primary_label import PrimaryLabel
from gui.widgets.controls.primary_lineedit import PrimaryLineEdit
from gui.widgets.controls.secondary_button import SecondaryButton
from gui.themes.theme_manager import ThemeManager
from repositories.can_interface_ui_store import CanInterfaceUiStore
from gui.widgets.can_interface.panel_theme import apply_panel_theme


class _SequenceList(QListWidget):
    checkbox_click = False

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        self.checkbox_click = False
        if item is not None:
            option = QStyleOptionViewItem()
            self.initViewItemOption(option)
            option.rect = self.visualItemRect(item)
            option.features |= QStyleOptionViewItem.HasCheckIndicator
            rectangle = self.style().subElementRect(QStyle.SE_ItemViewItemCheckIndicator, option, self)
            self.checkbox_click = rectangle.contains(event.position().toPoint())
        super().mousePressEvent(event)


class CanSequenceSidebar(DiagnosticSequenceList):
    sequence_open_requested = Signal(str)
    checked_sequences_changed = Signal(tuple)
    order_save_requested = Signal(tuple)

    def __init__(self, repository=None, store=None):
        self.store = store if store is not None else CanInterfaceUiStore()
        self._saved_order = ()
        self._active_source = self.store.load().selected_id
        super().__init__(repository)

    def _setup_ui(self):
        super()._setup_ui()
        self.setMinimumWidth(180)
        self.title = PrimaryLabel("Test Sequence")
        self.edit_search = PrimaryLineEdit("Search...")
        self.layout().insertWidget(0, self.title)
        self.layout().insertWidget(1, self.edit_search)
        old = self.list_sequences
        self.list_sequences = _SequenceList()
        self.list_sequences.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_sequences.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_sequences.setDefaultDropAction(Qt.MoveAction)
        self.list_sequences.setDropIndicatorShown(True)
        self.list_sequences.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.layout().replaceWidget(old, self.list_sequences)
        old.hide()
        old.deleteLater()
        self.lbl_selected = PrimaryLabel("0 selected")
        self.btn_save_order = SecondaryButton("Save Order", height=30, width=90)
        self.layout().addWidget(self.lbl_selected)
        self.layout().addWidget(self.btn_save_order)
        self.feedback = PrimaryLabel("")
        self.lbl_error.setTextFormat(Qt.PlainText)
        self.feedback.setTextFormat(Qt.PlainText)
        self.layout().addWidget(self.feedback)
        self.edit_search.textChanged.connect(self._filter)
        self.list_sequences.model().rowsMoved.connect(self._order_changed)
        self.list_sequences.itemActivated.connect(self._activate_item)
        self.btn_save_order.clicked.connect(self._save_order)
        self._feedback_timer = QTimer(self)
        self._feedback_timer.setSingleShot(True)
        self._feedback_timer.timeout.connect(self.feedback.clear)

    def source_ids(self):
        return tuple(self.list_sequences.item(i).data(self.ITEM_PATH_ROLE) for i in range(self.list_sequences.count()))

    def checked_ids(self):
        return tuple(self._selected_paths())

    def fn_refresh_sequences(self):
        pending = self.source_ids() if hasattr(self, 'list_sequences') and self.source_ids() != self._saved_order else ()
        super().fn_refresh_sequences()
        ids = self.source_ids()
        saved = self.store.load().order
        self._saved_order = tuple(x for x in saved if x in ids) + tuple(x for x in ids if x not in saved)
        self._apply_order(tuple(x for x in pending if x in ids) + tuple(x for x in self._saved_order if x not in pending)
                          if pending else self._saved_order)
        self._filter(self.edit_search.text())
        self._order_changed()
        self.mark_opened(self._active_source, persist=False)

    def _create_sequence_item(self, path, test_case):
        return super()._create_sequence_item(str(Path(path).resolve()), test_case)

    @staticmethod
    def _display_name(path, test_case):
        if test_case.name == Path(path).stem:
            return test_case.name
        return DiagnosticSequenceList._display_name(path, test_case)

    def _apply_order(self, ids):
        self._is_updating = True
        items = {self.list_sequences.item(i).data(self.ITEM_PATH_ROLE): self.list_sequences.item(i)
                 for i in range(self.list_sequences.count())}
        for position, source_id in enumerate(ids):
            item = items[source_id]
            self.list_sequences.takeItem(self.list_sequences.row(item))
            self.list_sequences.insertItem(position, item)
        self._is_updating = False

    def reorder(self, ids):
        ids = tuple(ids)
        if self.edit_search.text() or len(ids) != len(self.source_ids()) or set(ids) != set(self.source_ids()):
            return False
        self._apply_order(ids)
        self.mark_opened(self._active_source, persist=False)
        self._order_changed()
        return True

    def _order_changed(self, *_):
        if not self._is_updating:
            dirty = self.source_ids() != self._saved_order
            self.btn_save_order.setEnabled(dirty)
            self.btn_save_order.setText("Save Order *" if dirty else "Save Order")

    def _save_order(self):
        ids = self.source_ids()
        self.order_save_requested.emit(ids)
        try:
            self.store.save_order(ids)
        except OSError as error:
            self.feedback.setText(f"Cannot save order: {error}")
            return
        self._saved_order = ids
        self._order_changed()
        self.feedback.setText("Order saved.")
        self._feedback_timer.start(1800)

    def mark_opened(self, source_id, *, persist=True):
        self._active_source = source_id
        for index, item_id in enumerate(self.source_ids()):
            if item_id == source_id:
                self.list_sequences.setCurrentRow(index)
                break
        else:
            self.list_sequences.setCurrentRow(-1)
            self.list_sequences.clearSelection()
        if persist:
            try:
                self.store.save_selection(source_id)
            except OSError as error:
                self.feedback.setText(f"Cannot save selection: {error}")

    def _on_item_clicked(self, item):
        if self.list_sequences.checkbox_click:
            return
        self._activate_item(item)

    def _activate_item(self, item):
        self.sequence_open_requested.emit(item.data(self.ITEM_PATH_ROLE))
        self.sequence_selected.emit(item.data(self.ITEM_MODEL_ROLE))

    def _visible_items(self):
        return [self.list_sequences.item(i) for i in range(self.list_sequences.count())
                if not self.list_sequences.item(i).isHidden()]

    def _filter(self, text):
        for index in range(self.list_sequences.count()):
            item = self.list_sequences.item(index)
            item.setHidden(text.casefold() not in item.text().casefold())
        self.list_sequences.setDragEnabled(not bool(text))
        self.list_sequences.setAcceptDrops(not bool(text))
        self._sync_select_all_state()

    def _on_select_all_toggled(self, checked):
        if self._is_updating:
            return
        self._is_updating = True
        for item in self._visible_items():
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        self._is_updating = False
        self._sync_select_all_state()
        self._emit_selection_changed()

    def fn_clear_selection(self):
        self._on_select_all_toggled(False)

    def _sync_select_all_state(self):
        items = self._visible_items()
        self.chk_select_all.blockSignals(True)
        self.chk_select_all.setChecked(bool(items) and all(x.checkState() == Qt.Checked for x in items))
        self.chk_select_all.setText("Select All (visible)")
        self.chk_select_all.setEnabled(bool(items))
        self.chk_select_all.blockSignals(False)

    def _emit_selection_changed(self):
        super()._emit_selection_changed()
        ids = self.checked_ids()
        self.lbl_selected.setText(f"{len(ids)} selected")
        self.checked_sequences_changed.emit(ids)

    def fn_refresh_theme(self):
        apply_panel_theme(self, "canSequenceSidebar")
        super().fn_refresh_theme()
        for widget in (self.title, self.edit_search, self.lbl_selected, self.btn_save_order, self.feedback):
            widget.fn_refresh_theme()
        self.list_sequences.setStyleSheet(self.list_sequences.styleSheet() +
            f"QListWidget::drop-indicator {{ background: {ThemeManager.fn_colors().PRIMARY}; height: 2px; }}")
