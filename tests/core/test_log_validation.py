import tempfile
import unittest
from pathlib import Path

from core.log_validation import has_multiple_pt_bo_info_markers


class LogValidationTests(unittest.TestCase):

    def _write_log(self, content: str) -> Path:
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".asc",
            encoding="utf-8",
            delete=False,
        )
        self.addCleanup(Path(handle.name).unlink, missing_ok=True)
        handle.write(content)
        handle.close()
        return Path(handle.name)

    def test_accepts_log_with_one_pt_bo_info_marker(self):
        log_file = self._write_log("PT BO INFO\n1.0 1 681 Rx d 8 03 22 F1 90\n")

        self.assertFalse(has_multiple_pt_bo_info_markers(log_file))

    def test_rejects_log_with_multiple_pt_bo_info_markers(self):
        log_file = self._write_log("PT BO INFO\nPT BO INFO\n")

        self.assertTrue(has_multiple_pt_bo_info_markers(log_file))
