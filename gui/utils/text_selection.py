from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QLineEdit, QPlainTextEdit, QTextEdit


class _ClearTextSelectionOnFocusOut(QObject):

    def eventFilter(self, watched, event):
        if event.type() == QEvent.FocusOut:
            _clear_text_selection(watched)

        return False


def clear_text_selection_on_focus_out(parent, widgets):
    for widget in widgets:
        if getattr(widget, "_has_focus_out_selection_clear", False):
            continue
        event_filter = _ClearTextSelectionOnFocusOut(widget)
        widget.installEventFilter(event_filter)
        widget._has_focus_out_selection_clear = True


def _clear_text_selection(widget):
    if isinstance(widget, QLineEdit):
        widget.deselect()
        return

    if isinstance(widget, (QPlainTextEdit, QTextEdit)):
        cursor = widget.textCursor()
        cursor.clearSelection()
        widget.setTextCursor(cursor)
