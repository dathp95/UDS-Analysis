from PySide6.QtWidgets import QDialog, QVBoxLayout

from config.paths import SHORTCUTS_FILE
from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.cancel_button import CancelButton
from gui.widgets.controls.primary_label import PrimaryLabel
from shortcuts.shortcut_manager import load_shortcuts


class ShortcutsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.resize(420, 360)
        layout = QVBoxLayout(self)
        for item in load_shortcuts(SHORTCUTS_FILE):
            layout.addWidget(PrimaryLabel(
                f"{item.get('key', '')}  →  {item.get('label', item.get('action', ''))}"
            ))
        layout.addStretch()
        self.btn_close = CancelButton("Close", width=100)
        layout.addWidget(self.btn_close)
        self.btn_close.clicked.connect(self.reject)
        self.fn_refresh_theme()

    def fn_refresh_theme(self):
        self.btn_close.fn_refresh_theme()
