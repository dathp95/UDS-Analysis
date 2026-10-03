import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from core.coding_value_workspace import CodingEcuWorkspace
from core.coding_value_workspace_store import (
    CODING_WORKSPACE_CONFIG_VERSION,
    CodingWorkspaceState,
    CodingWorkspaceStore,
)
from core.coding_value_workspace_snapshot import (
    CodingWorkspaceRowSnapshot,
    CodingWorkspaceSnapshot,
)


class CodingWorkspaceStoreTests(unittest.TestCase):

    def test_missing_config_returns_none_without_creating_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "coding_value_workspaces.json"
            store = CodingWorkspaceStore(config_file)

            self.assertIsNone(store.load())
            self.assertFalse(config_file.exists())

    def test_save_then_load_round_trips_workspace_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "coding_value_workspaces.json"
            mhu = CodingEcuWorkspace("mhu-id", "MHU", "config/Coding/MHU.json")
            vcu = CodingEcuWorkspace("vcu-id", "VCU", "config/Coding/VCU.json")
            store = CodingWorkspaceStore(config_file)

            store.save(CodingWorkspaceState((mhu, vcu), "vcu-id"))
            loaded = store.load()

            self.assertEqual(loaded.active_workspace_id, "vcu-id")
            self.assertEqual(
                [(workspace.id, workspace.name, workspace.coding_file) for workspace in loaded.workspaces],
                [
                    ("mhu-id", "MHU", "config/Coding/MHU.json"),
                    ("vcu-id", "VCU", "config/Coding/VCU.json"),
                ],
            )
            self.assertFalse(config_file.with_name("coding_value_workspaces.json.tmp").exists())

    def test_save_file_schema_contains_only_persistent_workspace_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "coding_value_workspaces.json"
            store = CodingWorkspaceStore(config_file)
            store.save(CodingWorkspaceState((
                CodingEcuWorkspace("mhu-id", "MHU", "config/Coding/MHU.json"),
            ), "mhu-id"))

            payload = json.loads(config_file.read_text(encoding="utf-8"))

            self.assertEqual(payload["version"], CODING_WORKSPACE_CONFIG_VERSION)
            self.assertEqual(payload["active_workspace_id"], "mhu-id")
            self.assertEqual(payload["workspaces"], [
                {
                    "id": "mhu-id",
                    "name": "MHU",
                    "coding_file": "config/Coding/MHU.json",
                },
            ])

    def test_valid_empty_config_restores_empty_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "coding_value_workspaces.json"
            config_file.write_text(
                json.dumps({
                    "version": 1,
                    "workspaces": [],
                    "active_workspace_id": None,
                }),
                encoding="utf-8",
            )

            loaded = CodingWorkspaceStore(config_file).load()

            self.assertEqual(loaded, CodingWorkspaceState((), None))

    def test_corrupt_or_unsupported_config_returns_none_without_overwriting(self):
        payloads = [
            "{ bad json",
            json.dumps({"version": 2, "workspaces": []}),
            json.dumps([]),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "coding_value_workspaces.json"
            store = CodingWorkspaceStore(config_file)
            for payload in payloads:
                with self.subTest(payload=payload):
                    config_file.write_text(payload, encoding="utf-8")

                    self.assertIsNone(store.load())
                    self.assertEqual(config_file.read_text(encoding="utf-8"), payload)

    def test_partially_invalid_entries_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "coding_value_workspaces.json"
            config_file.write_text(
                json.dumps({
                    "version": 1,
                    "workspaces": [
                        {"id": "mhu-id", "name": "MHU", "coding_file": "mhu.json"},
                        {"id": "blank-name", "name": " ", "coding_file": "bad.json"},
                        {"id": "vcu-id", "name": "VCU", "coding_file": "vcu.json"},
                    ],
                    "active_workspace_id": "vcu-id",
                }),
                encoding="utf-8",
            )

            loaded = CodingWorkspaceStore(config_file).load()

            self.assertEqual(
                [(workspace.id, workspace.name) for workspace in loaded.workspaces],
                [("mhu-id", "MHU"), ("vcu-id", "VCU")],
            )
            self.assertEqual(loaded.active_workspace_id, "vcu-id")

    def test_non_empty_config_with_no_valid_workspaces_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "coding_value_workspaces.json"
            config_file.write_text(
                json.dumps({
                    "version": 1,
                    "workspaces": [
                        {"id": "blank-name", "name": " ", "coding_file": "bad.json"},
                    ],
                    "active_workspace_id": "blank-name",
                }),
                encoding="utf-8",
            )

            self.assertIsNone(CodingWorkspaceStore(config_file).load())

    def test_duplicate_ids_keep_first_and_duplicate_names_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "coding_value_workspaces.json"
            config_file.write_text(
                json.dumps({
                    "version": 1,
                    "workspaces": [
                        {"id": "vcu-a", "name": "VCU", "coding_file": "a.json"},
                        {"id": "vcu-a", "name": "VCU Duplicate ID", "coding_file": "bad.json"},
                        {"id": "vcu-b", "name": "VCU", "coding_file": "b.json"},
                    ],
                    "active_workspace_id": "vcu-b",
                }),
                encoding="utf-8",
            )

            loaded = CodingWorkspaceStore(config_file).load()

            self.assertEqual(
                [(workspace.id, workspace.name, workspace.coding_file) for workspace in loaded.workspaces],
                [
                    ("vcu-a", "VCU", "a.json"),
                    ("vcu-b", "VCU", "b.json"),
                ],
            )

    def test_invalid_active_id_falls_back_to_first_workspace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "coding_value_workspaces.json"
            config_file.write_text(
                json.dumps({
                    "version": 1,
                    "workspaces": [
                        {"id": "mhu-id", "name": "MHU", "coding_file": ""},
                        {"id": "vcu-id", "name": "VCU", "coding_file": ""},
                    ],
                    "active_workspace_id": "missing-id",
                }),
                encoding="utf-8",
            )

            loaded = CodingWorkspaceStore(config_file).load()

            self.assertEqual(loaded.active_workspace_id, "mhu-id")

    def test_project_internal_absolute_paths_are_saved_relative(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_file = project_root / "config" / "coding_value_workspaces.json"
            coding_file = project_root / "config" / "Coding" / "MHU.json"
            store = CodingWorkspaceStore(config_file, project_root=project_root)

            store.save(CodingWorkspaceState((
                CodingEcuWorkspace("mhu-id", "MHU", str(coding_file)),
            ), "mhu-id"))

            payload = json.loads(config_file.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["workspaces"][0]["coding_file"],
                "config/Coding/MHU.json",
            )

    def test_relative_paths_are_expanded_for_runtime_use(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            store = CodingWorkspaceStore(
                project_root / "config" / "coding_value_workspaces.json",
                project_root=project_root,
            )

            self.assertEqual(
                store.path_for_use("config/export_coding_files/mhu.json"),
                str(project_root / "config" / "export_coding_files" / "mhu.json"),
            )
            self.assertEqual(store.path_for_use(""), "")

    def test_workspace_snapshot_saves_loads_and_deletes_by_workspace_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            store = CodingWorkspaceStore(
                project_root / "config" / "coding_value_workspaces.json",
                project_root=project_root,
                snapshot_dir=project_root / "config" / "coding_value_workspace_snapshots",
            )
            coding_file = project_root / "config" / "export_coding_files" / "mhu.json"
            snapshot = CodingWorkspaceSnapshot(
                coding_file=str(coding_file),
                payload_input="62 F1 08 37",
                payload_preview="62 F1 08 FF",
                baseline_payload="62 F1 08 37",
                parameter_filter="No-M",
                checked=True,
                raw_values=(
                    CodingWorkspaceRowSnapshot("Param", "3", "0", "8", "FF"),
                ),
                working_log="Total No-M: 1",
            )

            store.save_snapshot("mhu-id", snapshot)
            loaded = store.load_snapshot("mhu-id")

            self.assertEqual(
                loaded.coding_file,
                "config/export_coding_files/mhu.json",
            )
            self.assertEqual(loaded.payload_preview, "62 F1 08 FF")
            self.assertEqual(loaded.raw_values[0].raw_value, "FF")
            self.assertEqual(
                store.snapshot_path("mhu-id").parent.name,
                "coding_value_workspace_snapshots",
            )

            store.delete_snapshot("mhu-id")

            self.assertIsNone(store.load_snapshot("mhu-id"))

    def test_invalid_snapshot_returns_none_without_breaking_store(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = CodingWorkspaceStore(
                Path(tmpdir) / "coding_value_workspaces.json",
                snapshot_dir=Path(tmpdir) / "snapshots",
            )
            path = store.snapshot_path("mhu-id")
            path.parent.mkdir(parents=True)
            path.write_text("{ bad json", encoding="utf-8")

            self.assertIsNone(store.load_snapshot("mhu-id"))
            self.assertEqual(path.read_text(encoding="utf-8"), "{ bad json")

    def test_store_module_has_no_qt_dependency(self):
        sys.modules.pop("core.coding_value_workspace_store", None)
        before = {name for name in sys.modules if name.startswith("PySide6")}

        importlib.import_module("core.coding_value_workspace_store")

        after = {name for name in sys.modules if name.startswith("PySide6")}
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
