from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QFrame,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.coding_value_workspace import CodingEcuWorkspace
from gui.themes.styles.controls.menu_style import fn_apply_menu_style
from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style
from gui.themes.theme_manager import ThemeManager
from gui.widgets.controls.quick_access_button import QuickAccessButton
from gui.widgets.controls.secondary_button import SecondaryButton


class EcuWorkspaceItemWidget(QuickAccessButton):

    clicked = Signal(str)
    save_requested = Signal(str)
    delete_requested = Signal(str)
    rename_requested = Signal(str)

    def __init__(self, workspace: CodingEcuWorkspace, parent=None):
        self.workspace = workspace
        self._active = False
        self._dirty = False
        super().__init__(workspace.name, width=132, height=26, parent=parent)
        self.setObjectName("ecuWorkspaceItem")
        self.setCursor(Qt.PointingHandCursor)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        super().clicked.connect(lambda checked=False: self.clicked.emit(self.workspace.id))
        self.setToolTip(self.workspace.name)

    def set_active(self, active: bool):
        self._active = active
        self.fn_refresh_theme()

    def set_dirty(self, dirty: bool):
        self._dirty = dirty
        self._refresh_text()

    def set_workspace_name(self, name: str):
        self._refresh_text()
        self.setToolTip(name)

    def workspace_name(self) -> str:
        return self.workspace.name

    def _refresh_text(self):
        suffix = " *" if self._dirty else ""
        self.setText(f"{self.workspace.name}{suffix}")

    def _show_context_menu(self, position):
        menu = self._create_context_menu()
        action = menu.exec(self.mapToGlobal(position))
        if action is None:
            return

        if action.text() == "Save":
            self.save_requested.emit(self.workspace.id)
        elif action.text() == "Rename":
            self.rename_requested.emit(self.workspace.id)
        elif action.text() == "Delete":
            self.delete_requested.emit(self.workspace.id)

    def _create_context_menu(self):
        menu = QMenu(self)
        fn_apply_menu_style(menu)
        menu.addAction("Save")
        menu.addSeparator()
        menu.addAction("Rename")
        menu.addAction("Delete")
        return menu

    def fn_refresh_theme(self):
        super().fn_refresh_theme()
        if not self._active:
            return

        colors = ThemeManager.fn_colors()
        self.setStyleSheet(
            f"""
            QPushButton#ecuWorkspaceItem {{
                background-color: {colors.TABLE_SELECTION};
                color: {colors.TEXT_INVERT};
                border: 1px solid {colors.BORDER};
                border-radius: 4px;
                font-family: "Segoe UI";
                font-size: 10pt;
                font-weight: 600;
                min-height: 24px;
                padding-left: 16px;
                padding-right: 10px;
                text-align: left;
            }}
            """
        )


class EcuWorkspaceSidebar(QWidget):

    workspace_added = Signal(object)
    workspace_selected = Signal(str)
    workspace_save_requested = Signal(str)
    workspace_renamed = Signal(str, str)
    workspace_deleted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._workspaces: list[CodingEcuWorkspace] = []
        self._active_workspace_id: str | None = None
        self._item_by_id: dict[str, EcuWorkspaceItemWidget] = {}
        self._setup_ui()
        self._connect_signals()
        self.fn_refresh_theme()

    def _setup_ui(self):
        self.setObjectName("ecuWorkspaceSidebar")
        self.setFixedWidth(170)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.lbl_title = QLabel("ECU")
        self.lbl_title.setObjectName("ecuWorkspaceTitle")
        self.btn_add = SecondaryButton("+ Add ECU", width=132, height=28)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(6, 6, 6, 6)
        self.list_layout.setSpacing(4)
        self.list_layout.addStretch(1)
        self.scroll_area.setWidget(self.list_container)

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.scroll_area, 1)
        layout.addWidget(self.btn_add)

    def _connect_signals(self):
        self.btn_add.clicked.connect(self._add_workspace_from_dialog)

    def workspace_count(self) -> int:
        return len(self._workspaces)

    def workspaces(self) -> list[CodingEcuWorkspace]:
        return list(self._workspaces)

    def workspace_by_id(self, workspace_id: str) -> CodingEcuWorkspace | None:
        for workspace in self._workspaces:
            if workspace.id == workspace_id:
                return workspace

        return None

    def active_workspace_id(self) -> str | None:
        return self._active_workspace_id

    def active_workspace(self) -> CodingEcuWorkspace | None:
        if self._active_workspace_id is None:
            return None

        return self.workspace_by_id(self._active_workspace_id)

    def add_workspace(
            self,
            workspace: CodingEcuWorkspace,
            select: bool = False,
        ) -> bool:
        if self.workspace_by_id(workspace.id) is not None:
            return False

        self._workspaces.append(workspace)
        item = EcuWorkspaceItemWidget(workspace)
        item.clicked.connect(self.select_workspace)
        item.save_requested.connect(self.workspace_save_requested)
        item.delete_requested.connect(self.remove_workspace)
        item.rename_requested.connect(self._rename_workspace_from_dialog)
        self._item_by_id[workspace.id] = item
        self.list_layout.insertWidget(
            max(0, self.list_layout.count() - 1),
            item,
        )
        self.fn_refresh_theme()
        if select:
            self.select_workspace(workspace.id)
        return True

    def set_workspace_dirty(self, workspace_id: str, dirty: bool):
        item = self._item_by_id.get(workspace_id)
        if item is not None:
            item.set_dirty(dirty)

    def select_workspace(
            self,
            workspace_id: str,
            emit_signal: bool = True,
        ) -> bool:
        if self.workspace_by_id(workspace_id) is None:
            return False

        self._active_workspace_id = workspace_id
        self._refresh_active_items()
        if emit_signal:
            self.workspace_selected.emit(workspace_id)
        return True

    def rename_workspace(
            self,
            workspace_id: str,
            name: str,
            emit_signal: bool = True,
        ) -> bool:
        workspace = self.workspace_by_id(workspace_id)
        if workspace is None:
            return False

        try:
            workspace.rename(name)
        except ValueError:
            return False

        item = self._item_by_id.get(workspace_id)
        if item is not None:
            item.set_workspace_name(workspace.name)
        if emit_signal:
            self.workspace_renamed.emit(workspace.id, workspace.name)
        return True

    def remove_workspace(
            self,
            workspace_id: str,
            emit_signal: bool = True,
        ) -> bool:
        removed_index = self._workspace_index(workspace_id)
        if removed_index < 0:
            return False

        was_active = self._active_workspace_id == workspace_id
        workspace = self._workspaces.pop(removed_index)
        item = self._item_by_id.pop(workspace.id, None)
        if item is not None:
            item.setParent(None)
            item.deleteLater()

        if was_active:
            self._select_fallback_after_delete(removed_index)
        else:
            self._refresh_active_items()

        if emit_signal:
            self.workspace_deleted.emit(workspace.id)
        return True

    def _workspace_index(self, workspace_id: str) -> int:
        for index, workspace in enumerate(self._workspaces):
            if workspace.id == workspace_id:
                return index

        return -1

    def _select_fallback_after_delete(self, removed_index: int):
        if not self._workspaces:
            self._active_workspace_id = None
            self._refresh_active_items()
            return

        fallback_index = min(removed_index, len(self._workspaces) - 1)
        self.select_workspace(self._workspaces[fallback_index].id)

    def _refresh_active_items(self):
        for workspace_id, item in self._item_by_id.items():
            item.set_active(workspace_id == self._active_workspace_id)

    def _item_widgets(self) -> list[EcuWorkspaceItemWidget]:
        return [
            self.list_layout.itemAt(index).widget()
            for index in range(self.list_layout.count())
            if isinstance(
                self.list_layout.itemAt(index).widget(),
                EcuWorkspaceItemWidget,
            )
        ]

    def _add_workspace_from_dialog(self):
        name, accepted = QInputDialog.getText(
            self,
            "Add ECU",
            "ECU name:",
        )
        if not accepted:
            return

        try:
            workspace = CodingEcuWorkspace.create(name)
        except ValueError:
            QMessageBox.warning(
                self,
                "Add ECU",
                "Please enter an ECU name.",
            )
            return

        self.add_workspace(workspace, select=False)
        self.workspace_added.emit(workspace)
        self.select_workspace(workspace.id)

    def _rename_workspace_from_dialog(self, workspace_id: str):
        workspace = self.workspace_by_id(workspace_id)
        if workspace is None:
            return

        name, accepted = QInputDialog.getText(
            self,
            "Rename ECU",
            "ECU name:",
            text=workspace.name,
        )
        if not accepted:
            return

        if not self.rename_workspace(workspace_id, name):
            QMessageBox.warning(
                self,
                "Rename ECU",
                "Please enter an ECU name.",
            )

    def fn_refresh_theme(self):
        colors = ThemeManager.fn_colors()
        self.setStyleSheet(
            f"""
            QWidget#ecuWorkspaceSidebar {{
                background-color: {colors.PANEL};
                border: 1px solid {colors.BORDER};
                border-radius: 6px;
            }}
            QLabel#ecuWorkspaceTitle {{
                color: {colors.TEXT};
                font-weight: 600;
            }}
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            """
        )
        self.lbl_title.setStyleSheet(
            f"""
            QLabel {{
                color: {colors.TEXT};
                font-weight: 600;
            }}
            """
        )
        self.btn_add.fn_refresh_theme()
        for item in self._item_widgets():
            item.fn_refresh_theme()
        fn_apply_scrollbar_style(self.scroll_area)
