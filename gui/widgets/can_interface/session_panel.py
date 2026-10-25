from PySide6.QtWidgets import QVBoxLayout, QWidget
from gui.widgets.can_interface.connection_panel import CanConnectionPanel
from gui.widgets.can_interface.current_test_case_panel import CurrentTestCasePanel
from gui.widgets.can_interface.panel_theme import apply_panel_theme


class CanSessionPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        self.connection = CanConnectionPanel()
        self.current_test_case = CurrentTestCasePanel()
        layout.addWidget(self.connection)
        layout.addWidget(self.current_test_case, 1)

    def fn_refresh_theme(self):
        apply_panel_theme(self, "canSessionPanel")
        self.connection.fn_refresh_theme()
        self.current_test_case.fn_refresh_theme()
