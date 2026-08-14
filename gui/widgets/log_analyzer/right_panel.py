from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)

from gui.widgets.log_analyzer.action_panel import ActionPanel


class RightPanel(QWidget):

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.action_panel = ActionPanel()

        main_layout.addWidget(
            self.action_panel,
            1,
        )

    def fn_refresh_theme(self):

        self.action_panel.fn_refresh_theme()
