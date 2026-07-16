
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout
)
from PySide6.QtCore import Signal
from gui.widgets.panels.action_panel import ActionPanel
from gui.widgets.controls.theme_switch import ThemeSwitch
from gui.widgets.quick_access import QuickAccessWidget

class RightPanel(QWidget):
    quick_filter_selected = Signal(dict)

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.action_panel = ActionPanel()
        lbl_title = QLabel("Right Panel")

        self.quick_access = QuickAccessWidget()

        self.theme_switch = ThemeSwitch()

        main_layout.addWidget(self.action_panel)
        main_layout.addWidget(self.quick_access)
       
        main_layout.addStretch() #Everything stays at the top.
        
        main_layout.addWidget(self.theme_switch)

        self._connect_signals()
    
    def _connect_signals(self):
        """
        Forward child widget signals.
        """

        self.quick_access.quick_filter_selected.connect(

            self.quick_filter_selected.emit

        )
    def fn_enable_quick_access(self):

        self.quick_access.fn_set_enabled()
    
    def fn_disable_quick_access(self):

        self.quick_access.fn_set_disabled()


    def fn_refresh_theme(self):

        self.action_panel.fn_refresh_theme()

        self.theme_switch.fn_refresh_theme()
