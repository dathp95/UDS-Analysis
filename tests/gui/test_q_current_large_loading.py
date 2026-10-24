import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QThread, QTimer
from PySide6.QtWidgets import QApplication, QTableView

from core.q_current_loading import prepare_workspace_data
from core.sleep_current_database import import_dataset
from gui.tabs.q_current_tab import QCurrentTab
from gui.themes.theme import ThemeType
from gui.themes.theme_manager import ThemeManager


class QCurrentLargeLoadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        directory = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2])
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.tab = QCurrentTab(database_dir=self.root / "db", config_file=self.root / "config.json")
        self.addCleanup(self.tab.deleteLater)
        self.addCleanup(ThemeManager.fn_set_theme, ThemeManager.fn_theme())

    def wait_for_idle(self):
        deadline = time.monotonic() + 20
        while self.tab._operation_running and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.001)
        self.assertFalse(self.tab._operation_running)

    def test_large_database_repeated_load_is_lazy_responsive_and_complete(self):
        database = self.root / "db" / "large.db"
        import_dataset("large", self.root / "large.csv",
                       [(str(i), 0.01, 10.0) for i in range(50000)], database)
        self.tab._refresh_dataset_combo(selected_db_path=database)
        threads, resets, ticks = [], [], []

        def prepare(samples):
            threads.append(QThread.currentThread() == self.app.thread())
            return prepare_workspace_data(samples)

        def reset():
            resets.append((QThread.currentThread() == self.app.thread(),
                           self.tab._operation_running,
                           self.tab.analysis_progress_bar.format()))

        self.tab.review_table.model().modelReset.connect(reset)
        timer = QTimer()
        timer.setInterval(5)
        timer.timeout.connect(lambda: ticks.append(time.perf_counter()))
        timer.start()
        try:
            with patch("gui.tabs.q_current_tab.prepare_workspace_data", side_effect=prepare), patch(
                "gui.tabs.q_current_tab.calculate_elapsed_seconds", side_effect=AssertionError("GUI timestamp scan")
            ):
                for theme in (ThemeType.DARK, ThemeType.LIGHT):
                    self.tab.load_selected_dataset()
                    ThemeManager.fn_set_theme(theme)
                    self.tab.fn_refresh_theme()
                    self.wait_for_idle()
                    self.assertEqual(self.tab.analysis_progress_bar.text(), "IMPORTED")
                    self.assertEqual(len(self.tab.current_samples), 50000)
                    model = self.tab.review_table.model()
                    self.assertIsInstance(self.tab.review_table, QTableView)
                    self.assertIs(model.samples, self.tab.current_samples)
                    self.assertLess(model.rowCount(), 50000)
                    model.fetchMore()
                    self.tab.review_table.selectRow(model.rowCount() - 1)
                    self.assertEqual(len(self.tab.review_table.selectionModel().selectedRows()), 1)
                    copied = self.tab._review_table_to_text().splitlines()
                    self.assertEqual(len(copied), 50001)
                    self.assertEqual(copied[-1], "50000\t49999\t10.00")
                    self.assertIn("sqlite_read_s", self.tab.last_loading_timings)
                    self.assertIn("prepare_s", self.tab.last_loading_timings)
                    self.assertIn("table_bind_s", self.tab.last_loading_timings)
                self.tab.sampling_duration_checkbox.setChecked(False)
                self.tab.analysis_end_time_edit.setValue(49999)
                self.tab.run_current_analysis()
                self.wait_for_idle()
                self.assertEqual(self.tab.current_analysis_result.total_samples, 50000)
                self.assertEqual(self.tab.analysis_progress_bar.text(), "PASSED")
        finally:
            timer.stop()
        self.assertEqual(threads, [False, False])
        self.assertEqual(resets, [(True, True, "IMPORTING..."), (True, True, "IMPORTING...")])
        self.assertGreater(len(ticks), 3)
        self.assertLess(max(b - a for a, b in zip(ticks, ticks[1:])), 2.0)

    def test_import_catalog_preparation_never_runs_on_gui_thread(self):
        source = self.root / "small.csv"
        source.write_text("Trigger time,No1 Average Ch1\n0,0.001\n1,0.002\n", encoding="utf-8")
        self.tab.set_source_file(source)
        import gui.tabs.q_current_tab as module
        original = module.list_datasets
        threads = []

        def catalog(*args):
            threads.append(QThread.currentThread() == self.app.thread())
            return original(*args)

        with patch.object(module, "list_datasets", side_effect=catalog), patch.object(module.QMessageBox, "information"):
            self.tab.import_current_file()
            self.wait_for_idle()
        self.assertEqual(threads, [False])
        self.assertEqual(self.tab.analysis_progress_bar.text(), "IMPORTED")
        self.assertIn("file_parse_s", self.tab.last_loading_timings)

    def test_invalid_timestamp_keeps_import_behavior_but_analysis_reports_error(self):
        from types import SimpleNamespace

        self.tab._load_samples_into_workspace([SimpleNamespace(time="bad", current_mA=1)])
        self.assertFalse(self.tab.analysis_start_time_edit.isEnabled())
        with patch("gui.tabs.q_current_tab.QMessageBox.warning") as warning:
            self.tab.run_current_analysis()
            self.wait_for_idle()
        warning.assert_called_once()
        self.assertEqual(self.tab.analysis_progress_bar.text(), "ANALYSIS ERROR")
