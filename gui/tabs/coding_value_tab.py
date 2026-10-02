from PySide6.QtWidgets import (
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.coding_value_workspace import CodingEcuWorkspace
from gui.widgets.coding_value.coding_value_panel import CodingValuePanel
from gui.widgets.coding_value.ecu_workspace_sidebar import EcuWorkspaceSidebar


class CodingValueTab(QWidget):

    def __init__(self):
        super().__init__()

        self._panel_by_workspace_id: dict[str, CodingValuePanel] = {}
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
        self.workspace_stack = QStackedWidget()
        self.workspace_sidebar.workspace_added.connect(self._add_workspace_panel)
        self.workspace_sidebar.workspace_selected.connect(self._select_workspace_panel)
        self.workspace_sidebar.workspace_deleted.connect(self._remove_workspace_panel)

        self.workspace_row = QWidget()
        workspace_layout = QHBoxLayout(self.workspace_row)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(12)
        workspace_layout.addWidget(self.workspace_sidebar, 0)
        workspace_layout.addWidget(self.workspace_stack, 1)

        main_layout.addWidget(
            self.workspace_row,
            1,
        )

        initial_workspace = CodingEcuWorkspace.create("ECU 1")
        self.workspace_sidebar.add_workspace(initial_workspace)
        self._add_workspace_panel(initial_workspace)
        self.workspace_sidebar.select_workspace(initial_workspace.id)

    @property
    def coding_value_panel(self) -> CodingValuePanel | None:
        return self.active_coding_value_panel()

    def active_coding_value_panel(self) -> CodingValuePanel | None:
        workspace_id = self.workspace_sidebar.active_workspace_id()
        if workspace_id is None:
            return None

        return self._panel_by_workspace_id.get(workspace_id)

    def _add_workspace_panel(self, workspace: CodingEcuWorkspace):
        if workspace.id in self._panel_by_workspace_id:
            return

        panel = CodingValuePanel()
        self._panel_by_workspace_id[workspace.id] = panel
        self.workspace_stack.addWidget(panel)

    def _remove_workspace_panel(self, workspace_id: str):
        panel = self._panel_by_workspace_id.pop(workspace_id, None)
        if panel is not None:
            self.workspace_stack.removeWidget(panel)
            panel.deleteLater()

        active_panel = self.active_coding_value_panel()
        if active_panel is not None:
            self.workspace_stack.setCurrentWidget(active_panel)

    def _select_workspace_panel(self, workspace_id: str):
        panel = self._panel_by_workspace_id.get(workspace_id)
        if panel is None:
            return

        self.workspace_stack.setCurrentWidget(panel)

    def fn_set_crc_value(self, crc_value):
        panel = self.active_coding_value_panel()
        if panel is None:
            return False

        return panel.fn_set_crc_value(crc_value)

    def fn_refresh_theme(self):
        self.workspace_sidebar.fn_refresh_theme()
        for panel in self._panel_by_workspace_id.values():
            panel.fn_refresh_theme()
