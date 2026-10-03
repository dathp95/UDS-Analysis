import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from core.coding_value_workspace import CodingEcuWorkspace
from gui.themes.theme_manager import ThemeManager
from gui.widgets.coding_value.ecu_workspace_sidebar import EcuWorkspaceSidebar
from gui.widgets.controls.quick_access_button import QuickAccessButton


class EcuWorkspaceSidebarTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_initial_empty_sidebar_has_add_control(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)

        self.assertEqual(sidebar.workspace_count(), 0)
        self.assertIsNone(sidebar.active_workspace_id())
        self.assertEqual(sidebar.lbl_title.text(), "PANEL")
        self.assertEqual(sidebar.btn_add.text(), "+ Add Panel")
        self.assertEqual(sidebar.btn_save.text(), "Save")
        self.assertFalse(sidebar.btn_save.isEnabled())
        root_layout = sidebar.layout()
        self.assertLess(
            root_layout.indexOf(sidebar.scroll_area),
            root_layout.indexOf(sidebar.btn_add),
        )
        self.assertLess(
            root_layout.indexOf(sidebar.btn_add),
            root_layout.indexOf(sidebar.btn_save),
        )
        self.assertLessEqual(sidebar.list_layout.spacing(), 4)

    def test_add_existing_workspace_preserves_id_and_display_name(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        workspace = CodingEcuWorkspace.create("MHU")

        sidebar.add_workspace(workspace)

        self.assertEqual(sidebar.workspace_count(), 1)
        self.assertIs(sidebar.workspaces()[0], workspace)
        self.assertIs(sidebar.workspace_by_id(workspace.id), workspace)
        self.assertEqual(sidebar._item_by_id[workspace.id].workspace_name(), "MHU")
        self.assertIsInstance(sidebar._item_by_id[workspace.id], QuickAccessButton)

    def test_multiple_workspaces_preserve_order(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        workspaces = [
            CodingEcuWorkspace.create(name)
            for name in ("MHU", "VCU", "BCM", "OBC")
        ]

        for workspace in workspaces:
            sidebar.add_workspace(workspace)

        self.assertEqual(sidebar.workspaces(), workspaces)
        self.assertEqual(
            [item.workspace_name() for item in sidebar._item_widgets()],
            ["MHU", "VCU", "BCM", "OBC"],
        )

    def test_selection_uses_workspace_id(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        mhu = CodingEcuWorkspace.create("MHU")
        vcu = CodingEcuWorkspace.create("VCU")
        sidebar.add_workspace(mhu)
        sidebar.add_workspace(vcu)
        selected = []
        sidebar.workspace_selected.connect(selected.append)

        self.assertTrue(sidebar.select_workspace(vcu.id))

        self.assertEqual(sidebar.active_workspace_id(), vcu.id)
        self.assertEqual(selected, [vcu.id])
        self.assertNotEqual(selected[0], "VCU")
        self.assertTrue(sidebar.btn_save.isEnabled())

    def test_rename_preserves_id_updates_model_and_emits(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        workspace = CodingEcuWorkspace.create("MHU")
        sidebar.add_workspace(workspace)
        renamed = []
        sidebar.workspace_renamed.connect(
            lambda workspace_id, name: renamed.append((workspace_id, name))
        )

        self.assertTrue(sidebar.rename_workspace(workspace.id, " Main Head Unit "))

        self.assertEqual(workspace.name, "Main Head Unit")
        self.assertEqual(sidebar._item_by_id[workspace.id].workspace_name(), "Main Head Unit")
        self.assertEqual(renamed, [(workspace.id, "Main Head Unit")])

    def test_delete_non_active_preserves_current_selection(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        mhu = CodingEcuWorkspace.create("MHU")
        vcu = CodingEcuWorkspace.create("VCU")
        bcm = CodingEcuWorkspace.create("BCM")
        for workspace in (mhu, vcu, bcm):
            sidebar.add_workspace(workspace)
        sidebar.select_workspace(mhu.id)

        self.assertTrue(sidebar.remove_workspace(bcm.id))

        self.assertEqual(sidebar.active_workspace_id(), mhu.id)
        self.assertEqual(sidebar.workspaces(), [mhu, vcu])

    def test_delete_active_selects_next_workspace_at_same_index(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        mhu = CodingEcuWorkspace.create("MHU")
        vcu = CodingEcuWorkspace.create("VCU")
        bcm = CodingEcuWorkspace.create("BCM")
        for workspace in (mhu, vcu, bcm):
            sidebar.add_workspace(workspace)
        sidebar.select_workspace(vcu.id)

        self.assertTrue(sidebar.remove_workspace(vcu.id))

        self.assertEqual(sidebar.active_workspace_id(), bcm.id)

    def test_delete_last_workspace_clears_active_state(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        workspace = CodingEcuWorkspace.create("MHU")
        sidebar.add_workspace(workspace, select=True)

        self.assertTrue(sidebar.remove_workspace(workspace.id))

        self.assertEqual(sidebar.workspace_count(), 0)
        self.assertIsNone(sidebar.active_workspace_id())

    def test_duplicate_names_keep_distinct_identity(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        first = CodingEcuWorkspace.create("VCU")
        second = CodingEcuWorkspace.create("VCU")
        sidebar.add_workspace(first)
        sidebar.add_workspace(second)

        sidebar.select_workspace(second.id)
        sidebar.remove_workspace(first.id)

        self.assertEqual(sidebar.workspace_count(), 1)
        self.assertEqual(sidebar.workspaces()[0].id, second.id)
        self.assertEqual(sidebar.active_workspace_id(), second.id)

    def test_arbitrary_number_of_workspaces_is_supported(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)

        for index in range(20):
            sidebar.add_workspace(CodingEcuWorkspace.create(f"ECU {index + 1}"))

        self.assertEqual(sidebar.workspace_count(), 20)

    def test_theme_refresh_is_safe_for_empty_and_active_sidebar(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)

        sidebar.fn_refresh_theme()
        workspace = CodingEcuWorkspace.create("MHU")
        sidebar.add_workspace(workspace, select=True)
        sidebar.fn_refresh_theme()

        self.assertEqual(sidebar.active_workspace_id(), workspace.id)

    def test_workspace_rows_are_compact_buttons_without_permanent_delete_button(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        workspace = CodingEcuWorkspace.create("MHU")

        sidebar.add_workspace(workspace, select=True)

        item = sidebar._item_by_id[workspace.id]
        self.assertIsInstance(item, QuickAccessButton)
        self.assertLessEqual(item.minimumHeight(), 28)
        self.assertFalse(hasattr(item, "btn_delete"))
        self.assertFalse(item.findChildren(QPushButton))
        self.assertNotIn("*", item.text())

    def test_workspace_context_menu_exposes_add_save_rename_and_delete_actions(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        workspace = CodingEcuWorkspace.create("MHU")
        sidebar.add_workspace(workspace)
        item = sidebar._item_by_id[workspace.id]

        menu = item._create_context_menu()
        actions = [action.text() for action in menu.actions()]

        self.assertEqual(actions, ["+ Add Panel", "", "Save", "", "Rename", "Delete"])
        menu.deleteLater()

    def test_workspace_context_menu_add_panel_uses_sidebar_add_workflow(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        workspace = CodingEcuWorkspace.create("MHU")
        sidebar.add_workspace(workspace)
        item = sidebar._item_by_id[workspace.id]
        called = []
        item.add_panel_requested.connect(lambda: called.append(True))

        menu = item._create_context_menu()
        with patch(
            "gui.widgets.coding_value.ecu_workspace_sidebar.QInputDialog.getText",
            return_value=("", False),
        ):
            menu.actions()[0].trigger()

        self.assertEqual(called, [True])
        menu.deleteLater()

    def test_workspace_save_request_emits_clicked_workspace_id_without_selecting(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        mhu = CodingEcuWorkspace.create("MHU")
        vcu = CodingEcuWorkspace.create("VCU")
        sidebar.add_workspace(mhu)
        sidebar.add_workspace(vcu, select=True)
        saved = []
        selected = []
        sidebar.workspace_save_requested.connect(saved.append)
        sidebar.workspace_selected.connect(selected.append)

        sidebar._item_by_id[mhu.id].save_requested.emit(mhu.id)

        self.assertEqual(saved, [mhu.id])
        self.assertEqual(selected, [])
        self.assertEqual(sidebar.active_workspace_id(), vcu.id)

    def test_sidebar_save_button_emits_active_workspace_id(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        mhu = CodingEcuWorkspace.create("MHU")
        vcu = CodingEcuWorkspace.create("VCU")
        sidebar.add_workspace(mhu)
        sidebar.add_workspace(vcu, select=True)
        saved = []
        sidebar.workspace_save_requested.connect(saved.append)

        sidebar.btn_save.click()

        self.assertEqual(saved, [vcu.id])
        self.assertEqual(sidebar.active_workspace_id(), vcu.id)

    def test_dirty_marker_is_visual_only_and_preserves_workspace_name(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        workspace = CodingEcuWorkspace.create("MHU")
        sidebar.add_workspace(workspace)
        item = sidebar._item_by_id[workspace.id]

        sidebar.set_workspace_dirty(workspace.id, True)

        self.assertEqual(item.workspace_name(), "MHU")
        self.assertEqual(item.text(), "MHU *")

        sidebar.set_workspace_dirty(workspace.id, False)

        self.assertEqual(item.text(), "MHU")

    def test_active_workspace_uses_theme_success_green(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        mhu = CodingEcuWorkspace.create("MHU")
        vcu = CodingEcuWorkspace.create("VCU")
        sidebar.add_workspace(mhu)
        sidebar.add_workspace(vcu)

        sidebar.select_workspace(mhu.id)

        self.assertIn(
            ThemeManager.fn_colors().SUCCESS,
            sidebar._item_by_id[mhu.id].styleSheet(),
        )
        self.assertNotIn(
            ThemeManager.fn_colors().SUCCESS,
            sidebar._item_by_id[vcu.id].styleSheet(),
        )

        sidebar.select_workspace(vcu.id)

        self.assertNotIn(
            ThemeManager.fn_colors().SUCCESS,
            sidebar._item_by_id[mhu.id].styleSheet(),
        )
        self.assertIn(
            ThemeManager.fn_colors().SUCCESS,
            sidebar._item_by_id[vcu.id].styleSheet(),
        )

    def test_add_button_creates_selects_and_emits_workspace(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        added = []
        selected = []
        events = []
        sidebar.workspace_added.connect(added.append)
        sidebar.workspace_selected.connect(selected.append)
        sidebar.workspace_added.connect(lambda workspace: events.append(("added", workspace.id)))
        sidebar.workspace_selected.connect(lambda workspace_id: events.append(("selected", workspace_id)))

        with patch(
            "gui.widgets.coding_value.ecu_workspace_sidebar.QInputDialog.getText",
            return_value=(" VCU ", True),
        ):
            sidebar.btn_add.click()

        self.assertEqual(sidebar.workspace_count(), 1)
        self.assertEqual(sidebar.workspaces()[0].name, "VCU")
        self.assertEqual(added, [sidebar.workspaces()[0]])
        self.assertEqual(selected, [sidebar.workspaces()[0].id])
        self.assertEqual(events, [
            ("added", sidebar.workspaces()[0].id),
            ("selected", sidebar.workspaces()[0].id),
        ])

    def test_cancel_add_dialog_does_nothing(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        added = []
        sidebar.workspace_added.connect(added.append)

        with patch(
            "gui.widgets.coding_value.ecu_workspace_sidebar.QInputDialog.getText",
            return_value=("", False),
        ):
            sidebar.btn_add.click()

        self.assertEqual(sidebar.workspace_count(), 0)
        self.assertEqual(added, [])


if __name__ == "__main__":
    unittest.main()
