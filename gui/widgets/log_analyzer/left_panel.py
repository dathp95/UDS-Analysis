from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from gui.widgets.log_analyzer.quick_access import QuickAccessWidget



class LeftPanel(QWidget):
    quick_filter_selected = Signal(dict)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.quick_access = QuickAccessWidget()

        layout.addWidget(self.quick_access, 1)
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
        self.quick_access.fn_refresh_theme()
