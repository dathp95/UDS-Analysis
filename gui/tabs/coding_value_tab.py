from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from core.coding_value_workspace import CodingEcuWorkspace
from gui.widgets.coding_value.coding_value_panel import CodingValuePanel
from gui.widgets.coding_value.ecu_workspace_sidebar import EcuWorkspaceSidebar


class CodingValueTab(QWidget):

    def __init__(self):
        super().__init__()

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )
        main_layout.setSpacing(12)

        self.workspace_sidebar = EcuWorkspaceSidebar()
        self.coding_value_panel = CodingValuePanel()
        self.workspace_sidebar.add_workspace(
            CodingEcuWorkspace.create("ECU 1"),
            select=True,
        )

        self.workspace_row = QWidget()
        workspace_layout = QHBoxLayout(self.workspace_row)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(12)
        workspace_layout.addWidget(self.workspace_sidebar, 0)
        workspace_layout.addWidget(self.coding_value_panel, 1)

        main_layout.addWidget(
            self.workspace_row,
            1,
        )

    def fn_set_crc_value(self, crc_value):
        return self.coding_value_panel.fn_set_crc_value(crc_value)

    def fn_refresh_theme(self):
        self.workspace_sidebar.fn_refresh_theme()
        self.coding_value_panel.fn_refresh_theme()
