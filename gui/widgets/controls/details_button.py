from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QPushButton, QSizePolicy

from gui.themes.styles.controls.details_button_style import (
    fn_details_button_style,
)


class DetailsButton(QPushButton):

    expandedChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._expanded = False
        self._setup_ui()
        self.clicked.connect(self._toggle_expanded)

    def _setup_ui(self):
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        self.setMinimumHeight(28)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._update_text()
        self.fn_refresh_theme()

    def _toggle_expanded(self):
        self.set_expanded(not self._expanded)

    def set_expanded(self, expanded):
        expanded = bool(expanded)
        if self._expanded == expanded:
            return

        self._expanded = expanded
        self._update_text()
        self.expandedChanged.emit(self._expanded)

    def is_expanded(self):
        return self._expanded

    def fn_refresh_theme(self):
        self.setStyleSheet(fn_details_button_style())

    def _update_text(self):
        marker = "^" if self._expanded else ">"
        self.setText(f"{marker} Details")
