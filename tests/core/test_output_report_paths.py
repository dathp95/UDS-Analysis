import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config.paths import (
    CODING_VALUE_REPORT_DIR,
    CONFIG_DIR,
    LOG_ANALYZER_REPORT_DIR,
    OUTPUT_DIR,
    Q_CURRENT_DATABASE_DIR,
    Q_CURRENT_DATABASE_FILE,
)
from core.services.report_service import ReportService
from core.services.startup_service import ensure_directories


class OutputReportPathTests(unittest.TestCase):

    def test_report_and_q_current_database_paths_are_split_by_feature(self):
        self.assertEqual(
            LOG_ANALYZER_REPORT_DIR,
            OUTPUT_DIR / "Report_LogAnalyzer",
        )
        self.assertEqual(
            CODING_VALUE_REPORT_DIR,
            OUTPUT_DIR / "Report_CodingValue",
        )
        self.assertEqual(
            Q_CURRENT_DATABASE_DIR,
            CONFIG_DIR / "database_qcurrent",
        )
        self.assertEqual(
            Q_CURRENT_DATABASE_FILE,
            Q_CURRENT_DATABASE_DIR / "sleep_current.db",
        )

    def test_startup_creates_current_output_and_q_current_database_folders(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "output"
            log_report_dir = output_dir / "Report_LogAnalyzer"
            coding_report_dir = output_dir / "Report_CodingValue"
            q_current_database_dir = root / "config" / "database_qcurrent"

            with patch(
                "core.services.startup_service.OUTPUT_DIR",
                output_dir,
            ), patch(
                "core.services.startup_service.LOG_ANALYZER_REPORT_DIR",
                log_report_dir,
            ), patch(
                "core.services.startup_service.CODING_VALUE_REPORT_DIR",
                coding_report_dir,
            ), patch(
                "core.services.startup_service.Q_CURRENT_DATABASE_DIR",
                q_current_database_dir,
            ):
                ensure_directories()

            self.assertTrue(log_report_dir.exists())
            self.assertTrue(coding_report_dir.exists())
            self.assertTrue(q_current_database_dir.exists())
            self.assertFalse((output_dir / "Reports").exists())
            self.assertFalse((output_dir / "Logs").exists())
            self.assertFalse((output_dir / "Temp").exists())
            self.assertFalse((output_dir / "Cache").exists())

    def test_log_analyzer_report_service_uses_log_analyzer_folder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report_root = Path(tmpdir) / "Report_LogAnalyzer"

            with patch(
                "core.services.report_service.LOG_ANALYZER_REPORT_DIR",
                report_root,
            ):
                report_folder = ReportService().fn_get_report_folder()

            self.assertEqual(report_folder.parent, report_root)
            self.assertTrue(report_folder.exists())


if __name__ == "__main__":
    unittest.main()
