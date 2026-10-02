import unittest

from core.coding_value_workspace import CodingEcuWorkspace


class CodingEcuWorkspaceTests(unittest.TestCase):

    def test_create_workspace_has_id_name_and_empty_coding_file(self):
        workspace = CodingEcuWorkspace.create("MHU")

        self.assertTrue(workspace.id)
        self.assertEqual(workspace.name, "MHU")
        self.assertEqual(workspace.coding_file, "")

    def test_create_workspaces_use_unique_ids(self):
        workspace_a = CodingEcuWorkspace.create("MHU")
        workspace_b = CodingEcuWorkspace.create("VCU")

        self.assertNotEqual(workspace_a.id, workspace_b.id)

    def test_create_normalizes_surrounding_name_whitespace(self):
        workspace = CodingEcuWorkspace.create("  MHU  ")

        self.assertEqual(workspace.name, "MHU")

    def test_create_rejects_empty_names(self):
        with self.assertRaises(ValueError):
            CodingEcuWorkspace.create("")

        with self.assertRaises(ValueError):
            CodingEcuWorkspace.create("   ")

    def test_rename_preserves_id(self):
        workspace = CodingEcuWorkspace.create("MHU")
        original_id = workspace.id

        workspace.rename(" Main Head Unit ")

        self.assertEqual(workspace.id, original_id)
        self.assertEqual(workspace.name, "Main Head Unit")

    def test_coding_file_is_retained_without_loading_file(self):
        workspace = CodingEcuWorkspace.create(
            "MHU",
            coding_file=" config/export_coding_files/MHU.json ",
        )

        self.assertEqual(
            workspace.coding_file,
            "config/export_coding_files/MHU.json",
        )

        workspace.set_coding_file("config/export_coding_files/MHU_v2.json")

        self.assertEqual(
            workspace.coding_file,
            "config/export_coding_files/MHU_v2.json",
        )

    def test_two_workspaces_keep_independent_state(self):
        workspace_a = CodingEcuWorkspace.create(
            "MHU",
            coding_file="config/export_coding_files/MHU.json",
        )
        workspace_b = CodingEcuWorkspace.create(
            "VCU",
            coding_file="config/export_coding_files/VCU.json",
        )

        workspace_a.rename("Main Head Unit")
        workspace_a.set_coding_file("config/export_coding_files/MHU_v2.json")

        self.assertEqual(workspace_a.name, "Main Head Unit")
        self.assertEqual(
            workspace_a.coding_file,
            "config/export_coding_files/MHU_v2.json",
        )
        self.assertEqual(workspace_b.name, "VCU")
        self.assertEqual(
            workspace_b.coding_file,
            "config/export_coding_files/VCU.json",
        )

    def test_dict_round_trip_preserves_identity_name_and_coding_file(self):
        workspace = CodingEcuWorkspace.create(
            "MHU",
            coding_file="config/export_coding_files/MHU.json",
        )

        loaded = CodingEcuWorkspace.from_dict(workspace.to_dict())

        self.assertEqual(loaded.id, workspace.id)
        self.assertEqual(loaded.name, "MHU")
        self.assertEqual(
            loaded.coding_file,
            "config/export_coding_files/MHU.json",
        )


if __name__ == "__main__":
    unittest.main()
