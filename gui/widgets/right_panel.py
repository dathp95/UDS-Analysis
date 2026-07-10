
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout
)

from gui.widgets.panels.action_panel import ActionPanel
from gui.widgets.controls.theme_switch import ThemeSwitch

class RightPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.action_panel = ActionPanel()
        lbl_title = QLabel("Right Panel")

        self.theme_switch = ThemeSwitch()

        main_layout.addWidget(self.action_panel)
        main_layout.addWidget(self.theme_switch)
        main_layout.addStretch() #Everything stays at the top.
    
    def fn_refresh_theme(self):

        self.action_panel.fn_refresh_theme()

        self.theme_switch.fn_refresh_theme()
