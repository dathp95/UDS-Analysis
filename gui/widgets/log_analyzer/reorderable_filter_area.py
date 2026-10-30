from PySide6.QtCore import QEvent, QMimeData, QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QApplication, QFrame, QScrollArea

from gui.themes.theme_manager import ThemeManager


class ReorderableFilterArea(QScrollArea):
    """Keep real filter buttons while using Qt's native drag/drop lifecycle."""

    order_changed = Signal(list)
    MIME_TYPE = "application/x-vcode-quick-filter"

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.buttons = []
        self.reorder_enabled = True
        self._pressed_button = None
        self._press_position = QPoint()
        self._dragged = False
        self._drop_position = None
        self._scroll_direction = 0
        self._indicator = QFrame(self.viewport())
        self._indicator.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._indicator.hide()
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setInterval(40)
        self._scroll_timer.timeout.connect(self._fn_auto_scroll)
        self.fn_refresh_theme()

    def fn_set_buttons(self, buttons):
        self._fn_clear_drop()
        self._pressed_button = None
        for button in self.buttons:
            button.removeEventFilter(self)
        self.buttons = list(buttons)
        for button in self.buttons:
            button.installEventFilter(self)

    def fn_set_reorder_enabled(self, enabled):
        self.reorder_enabled = enabled
        if not enabled:
            self._fn_clear_drop()

    def fn_mime_data(self, button):
        mime = QMimeData()
        mime.setData(self.MIME_TYPE, str(button._quick_filter_data.get("id")).encode("ascii"))
        return mime

    def eventFilter(self, watched, event):
        if watched in self.buttons:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._pressed_button = watched
                self._press_position = event.position().toPoint()
                self._dragged = False
            elif event.type() == QEvent.MouseMove and (
                watched is self._pressed_button
                and event.buttons() & Qt.LeftButton
                and self.reorder_enabled and watched.isEnabled()
                and (event.position().toPoint() - self._press_position).manhattanLength()
                >= QApplication.startDragDistance()
            ):
                self._dragged = True
                watched.setDown(False)
                drag = QDrag(watched)
                drag.setMimeData(self.fn_mime_data(watched))
                drag.setPixmap(watched.grab())
                drag.setHotSpot(self._press_position)
                try:
                    drag.exec(Qt.MoveAction)
                finally:
                    watched.setDown(False)
                    self._pressed_button = None
                    self._fn_clear_drop()
                    drag.deleteLater()
                return True
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                self._pressed_button = None
                if self._dragged:
                    self._dragged = False
                    watched.setDown(False)
                    return True
            return False
        return super().eventFilter(watched, event)

    def _fn_accepts(self, event):
        source = event.source()
        return (self.reorder_enabled and self.isEnabled()
                and source in self.buttons and source.isEnabled()
                and event.mimeData().hasFormat(self.MIME_TYPE)
                and bool(event.possibleActions() & Qt.MoveAction))

    def dragEnterEvent(self, event):
        if self._fn_accepts(event):
            event.setDropAction(Qt.MoveAction)
            event.accept()
            self._fn_update_drop(event.position().toPoint())
        else:
            self._fn_clear_drop()
            event.ignore()

    def dragMoveEvent(self, event):
        self.dragEnterEvent(event)

    def dragLeaveEvent(self, event):
        self._fn_clear_drop()
        event.accept()

    def _fn_insertion_index(self, position):
        point = self.widget().mapFrom(self.viewport(), position)
        for index, button in enumerate(self.buttons):
            if point.y() < button.geometry().center().y():
                return index
        return len(self.buttons)

    def _fn_update_drop(self, position):
        self._drop_position = position
        index = self._fn_insertion_index(position)
        if not self.buttons:
            return
        button = self.buttons[min(index, len(self.buttons) - 1)]
        edge = button.rect().topLeft() if index < len(self.buttons) else button.rect().bottomLeft()
        point = button.mapTo(self.viewport(), edge)
        y = point.y() - 2 if index < len(self.buttons) else point.y() + 2
        y = max(0, min(y, self.viewport().height() - 3))
        self._indicator.setGeometry(point.x(), y, button.width(), 3)
        self._indicator.show()
        self._indicator.raise_()
        margin = 28
        self._scroll_direction = (-1 if position.y() < margin else
                                  1 if position.y() > self.viewport().height() - margin else 0)
        if self._scroll_direction:
            self._scroll_timer.start()
        else:
            self._scroll_timer.stop()

    def _fn_auto_scroll(self):
        bar = self.verticalScrollBar()
        bar.setValue(bar.value() + self._scroll_direction * max(8, bar.singleStep()))
        if self._drop_position is not None:
            self._fn_update_drop(self._drop_position)

    def dropEvent(self, event):
        if not self._fn_accepts(event):
            self._fn_clear_drop()
            event.ignore()
            return
        source = event.source()
        old_index = self.buttons.index(source)
        index = self._fn_insertion_index(event.position().toPoint())
        if index > old_index:
            index -= 1
        if index != old_index:
            self.buttons.pop(old_index)
            self.buttons.insert(index, source)
            self.widget().layout().insertWidget(index, source)
            self.order_changed.emit(list(self.buttons))
        self._fn_clear_drop()
        event.setDropAction(Qt.MoveAction)
        event.accept()

    def _fn_clear_drop(self):
        self._scroll_timer.stop()
        self._scroll_direction = 0
        self._drop_position = None
        self._indicator.hide()

    def fn_refresh_theme(self):
        self._indicator.setStyleSheet(f"background-color: {ThemeManager.fn_colors().PRIMARY};")
