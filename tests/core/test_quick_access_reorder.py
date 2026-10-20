import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from core.services.quick_access_service import QuickAccessService


class QuickAccessReorderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2])
        self.addCleanup(self.directory.cleanup)
        self.service = QuickAccessService()
        self.service.json_file = Path(self.directory.name) / "filters.json"
        self.filters = [
            {"id": i, "name": f"Filter {i}", "enabled": i != 2,
             "filters": {"ecu": "BCM", "request": "22 F1 90", "response": "62 F1 90"},
             "metadata": {"custom": [i]}}
            for i in (1, 2, 3)
        ]
        self.service.fn_save(self.filters)

    def test_reorder_preserves_full_data_and_survives_reload(self):
        original = deepcopy(self.filters)
        self.service.fn_reorder([3, 1, 2])
        restarted = QuickAccessService()
        restarted.json_file = self.service.json_file
        self.assertEqual(restarted.fn_load(), [original[2], original[0], original[1]])

    def test_rejects_duplicate_missing_unknown_and_invalid_ids_without_writing(self):
        original = self.service.json_file.read_bytes()
        for ids in ([1, 1, 3], [1, 2], [1, 2, 9], [True, 2, 3], ["1", 2, 3]):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                self.service.fn_reorder(ids)
            self.assertEqual(self.service.json_file.read_bytes(), original)

    def test_rejects_duplicate_stored_ids(self):
        self.service.fn_save([self.filters[0], self.filters[0]])
        with self.assertRaises(ValueError):
            self.service.fn_reorder([1, 1])

    def test_replace_failure_keeps_original_and_cleans_temporary_file(self):
        original = self.service.json_file.read_bytes()
        with patch("core.services.quick_access_service.os.replace", side_effect=OSError("locked")):
            with self.assertRaises(OSError):
                self.service.fn_reorder([3, 2, 1])
        self.assertEqual(self.service.json_file.read_bytes(), original)
        self.assertEqual(list(Path(self.directory.name).iterdir()), [self.service.json_file])


if __name__ == "__main__":
    unittest.main()
