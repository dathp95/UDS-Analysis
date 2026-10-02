import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from core.coding_value_workspace import CodingEcuWorkspace
from gui.widgets.coding_value.ecu_workspace_sidebar import EcuWorkspaceSidebar


class EcuWorkspaceSidebarTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_initial_empty_sidebar_has_add_control(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)

        self.assertEqual(sidebar.workspace_count(), 0)
        self.assertIsNone(sidebar.active_workspace_id())
        self.assertEqual(sidebar.btn_add.text(), "+ Add ECU")

    def test_add_existing_workspace_preserves_id_and_display_name(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        workspace = CodingEcuWorkspace.create("MHU")

        sidebar.add_workspace(workspace)

        self.assertEqual(sidebar.workspace_count(), 1)
        self.assertIs(sidebar.workspaces()[0], workspace)
        self.assertIs(sidebar.workspace_by_id(workspace.id), workspace)
        self.assertEqual(sidebar._item_by_id[workspace.id].workspace_name(), "MHU")

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

    def test_add_button_creates_selects_and_emits_workspace(self):
        sidebar = EcuWorkspaceSidebar()
        self.addCleanup(sidebar.deleteLater)
        added = []
        selected = []
        sidebar.workspace_added.connect(added.append)
        sidebar.workspace_selected.connect(selected.append)

        with patch(
            "gui.widgets.coding_value.ecu_workspace_sidebar.QInputDialog.getText",
            return_value=(" VCU ", True),
        ):
            sidebar.btn_add.click()

        self.assertEqual(sidebar.workspace_count(), 1)
        self.assertEqual(sidebar.workspaces()[0].name, "VCU")
        self.assertEqual(added, [sidebar.workspaces()[0]])
        self.assertEqual(selected, [sidebar.workspaces()[0].id])

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
