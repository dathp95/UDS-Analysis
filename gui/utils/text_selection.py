from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QLineEdit, QPlainTextEdit, QTextEdit


class _ClearTextSelectionOnFocusOut(QObject):

    def eventFilter(self, watched, event):
        if event.type() == QEvent.FocusOut:
            _clear_text_selection(watched)

        return super().eventFilter(watched, event)


def clear_text_selection_on_focus_out(parent, widgets):
    filters = getattr(parent, "_text_selection_clear_filters", [])
    for widget in widgets:
        event_filter = _ClearTextSelectionOnFocusOut(parent)
        widget.installEventFilter(event_filter)
        filters.append(event_filter)

    parent._text_selection_clear_filters = filters


def _clear_text_selection(widget):
    if isinstance(widget, QLineEdit):
        widget.deselect()
        return

    if isinstance(widget, (QPlainTextEdit, QTextEdit)):
        cursor = widget.textCursor()
        cursor.clearSelection()
        widget.setTextCursor(cursor)