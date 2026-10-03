from PySide6.QtWidgets import (
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.coding_value_workspace import CodingEcuWorkspace
from core.coding_value_workspace_store import (
    CodingWorkspaceState,
    CodingWorkspaceStore,
)
from gui.widgets.coding_value.coding_value_panel import CodingValuePanel
from gui.widgets.coding_value.ecu_workspace_sidebar import EcuWorkspaceSidebar


class CodingValueTab(QWidget):

    def __init__(self, workspace_store: CodingWorkspaceStore | None = None):
        super().__init__()

        self._workspace_store = workspace_store or CodingWorkspaceStore()
        self._panel_by_workspace_id: dict[str, CodingValuePanel] = {}
        self._restoring_workspaces = False
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
        self.workspace_sidebar.workspace_renamed.connect(
            lambda _workspace_id, _name: self._save_workspace_state()
        )

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

        self._restore_workspace_state()

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
        panel.coding_file_changed.connect(
            lambda coding_file, workspace_id=workspace.id:
                self._on_workspace_coding_file_changed(workspace_id, coding_file)
        )
        self._panel_by_workspace_id[workspace.id] = panel
        self.workspace_stack.addWidget(panel)
        if workspace.coding_file:
            panel.load_coding_definition_file(
                self._workspace_store.path_for_use(workspace.coding_file),
                emit_coding_file_changed=False,
            )
        self._save_workspace_state()

    def _remove_workspace_panel(self, workspace_id: str):
        panel = self._panel_by_workspace_id.pop(workspace_id, None)
        if panel is not None:
            self.workspace_stack.removeWidget(panel)
            panel.deleteLater()

        active_panel = self.active_coding_value_panel()
        if active_panel is not None:
            self.workspace_stack.setCurrentWidget(active_panel)
        self._save_workspace_state()

    def _select_workspace_panel(self, workspace_id: str):
        panel = self._panel_by_workspace_id.get(workspace_id)
        if panel is None:
            return

        self.workspace_stack.setCurrentWidget(panel)
        self._save_workspace_state()

    def _restore_workspace_state(self):
        self._restoring_workspaces = True
        try:
            state = self._workspace_store.load()
            if state is None:
                state = CodingWorkspaceState(
                    workspaces=(CodingEcuWorkspace.create("ECU 1"),),
                    active_workspace_id=None,
                )

            for workspace in state.workspaces:
                if not self.workspace_sidebar.add_workspace(workspace, select=False):
                    continue
                self._add_workspace_panel(workspace)

            active_workspace_id = (
                state.active_workspace_id
                if self.workspace_sidebar.workspace_by_id(state.active_workspace_id)
                else None
            )
            if active_workspace_id is None and state.workspaces:
                active_workspace_id = state.workspaces[0].id

            if active_workspace_id is not None:
                self.workspace_sidebar.select_workspace(
                    active_workspace_id,
                    emit_signal=False,
                )
                self._select_workspace_panel(active_workspace_id)
        finally:
            self._restoring_workspaces = False

    def _save_workspace_state(self):
        if self._restoring_workspaces:
            return

        self._workspace_store.save(
            CodingWorkspaceState(
                workspaces=tuple(self.workspace_sidebar.workspaces()),
                active_workspace_id=self.workspace_sidebar.active_workspace_id(),
            )
        )

    def _on_workspace_coding_file_changed(
            self,
            workspace_id: str,
            coding_file: str,
        ):
        workspace = self.workspace_sidebar.workspace_by_id(workspace_id)
        if workspace is None:
            return

        workspace.set_coding_file(coding_file)
        self._save_workspace_state()

    def fn_set_crc_value(self, crc_value):
        panel = self.active_coding_value_panel()
        if panel is None:
            return False

        return panel.fn_set_crc_value(crc_value)

    def fn_refresh_theme(self):
        self.workspace_sidebar.fn_refresh_theme()
        for panel in self._panel_by_workspace_id.values():
            panel.fn_refresh_theme()
