import os
import tempfile
import time
import unittest
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QThread, QTimer, Qt
from PySide6.QtWidgets import QApplication, QMessageBox, QProgressBar

from core.q_current_analysis import analyze_q_current
from core.sleep_current_database import normalize_current_data

from gui.tabs.q_current_tab import QCurrentTab
from gui.themes.theme import ThemeType
from gui.themes.theme_manager import ThemeManager


class QCurrentProgressTests(unittest.TestCase):
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
        deadline = time.monotonic() + 10
        while self.tab._operation_running and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.001)
        self.assertFalse(self.tab._operation_running)

    def test_initial_widget_and_all_state_ranges(self):
        bar = self.tab.analysis_progress_bar
        self.assertIsInstance(bar, QProgressBar)
        self.assertEqual(bar.objectName(), "analysis_progress_bar")
        self.assertEqual((bar.width(), bar.height()), (315, 36))
        self.assertEqual(bar.alignment(), Qt.AlignCenter)
        self.assertEqual(bar.text(), "NOT RUN")
        self.assertEqual(bar.value(), 0)
        for state, maximum, value, display in (
            ("IMPORTING", 0, 0, "IMPORTING..."),
            ("IMPORTED", 100, 100, "IMPORTED"),
            ("ANALYZING", 0, 0, "ANALYZING..."),
            ("PASSED", 100, 100, "PASSED"),
            ("FAILED", 100, 100, "FAILED"),
            ("IMPORT FAILED", 100, 0, "IMPORT FAILED"),
            ("ANALYSIS ERROR", 100, 0, "ANALYSIS ERROR"),
            ("NOT RUN", 100, 0, "NOT RUN"),
        ):
            with self.subTest(state=state):
                self.tab._set_analysis_result(state)
                self.assertEqual((bar.minimum(), bar.maximum(), bar.value()), (0, maximum, value))
                self.assertEqual(bar.format(), display)

    def test_theme_preserves_states_and_replaces_stylesheet(self):
        for theme in (ThemeType.DARK, ThemeType.LIGHT):
            ThemeManager.fn_set_theme(theme)
            for state in ("PASSED", "FAILED", "IMPORT FAILED", "ANALYSIS ERROR", "ANALYZING", "NOT RUN"):
                self.tab._set_analysis_result(state)
                before = self.tab.analysis_progress_bar.styleSheet()
                self.tab.fn_refresh_theme()
                self.tab.fn_refresh_theme()
                self.assertEqual(self.tab.analysis_progress_bar.styleSheet(), before)
                self.assertEqual(self.tab.analysis_progress_bar.format(), state + "..." if state == "ANALYZING" else state)
                color = (ThemeManager.fn_colors().SUCCESS if state == "PASSED" else
                         ThemeManager.fn_colors().DANGER if state in {"FAILED", "IMPORT FAILED", "ANALYSIS ERROR"}
                         else ThemeManager.fn_colors().PRIMARY if state == "ANALYZING" else ThemeManager.fn_colors().BORDER)
                self.assertIn(color, before)

    def load_samples(self, current_ma=10):
        self.tab.sampling_duration_checkbox.setChecked(False)
        self.tab._load_samples_into_workspace([
            SimpleNamespace(time=str(i), current_mA=current_ma) for i in range(5)
        ])

    def test_run_is_async_responsive_and_distinguishes_result_from_exception(self):
        self.load_samples()
        release = Event()
        calls = []

        def analyze(*args, **kwargs):
            calls.append(QThread.currentThread() == self.app.thread())
            if not release.wait(5):
                raise RuntimeError("test did not release worker")
            return analyze_q_current(*args, **kwargs)

        with patch("gui.tabs.q_current_tab.analyze_q_current", side_effect=analyze):
            try:
                self.tab.run_current_analysis()
                self.assertEqual(self.tab.analysis_progress_bar.format(), "ANALYZING...")
                self.assertFalse(self.tab.btn_run.isEnabled())
                self.assertFalse(self.tab.btn_clear.isEnabled())
                alive = []
                QTimer.singleShot(0, lambda: alive.append(True))
                self.app.processEvents()
                self.assertEqual(alive, [True])
                self.tab.run_current_analysis()
                self.tab.clear_current_workspace()
                self.assertEqual(len(self.tab.current_samples), 5)
            finally:
                release.set()
                self.wait_for_idle()
        self.assertEqual(calls, [False])
        self.assertEqual(self.tab.analysis_progress_bar.text(), "PASSED")
        self.assertTrue(self.tab.btn_run.isEnabled())
        self.assertTrue(self.tab.btn_export.isEnabled())
        self.load_samples(50)
        self.tab.run_current_analysis()
        self.wait_for_idle()
        self.assertEqual(self.tab.analysis_progress_bar.text(), "FAILED")
        previous = self.tab.current_analysis_result
        with patch("gui.tabs.q_current_tab.analyze_q_current", side_effect=RuntimeError("analysis failed")), patch(
            "gui.tabs.q_current_tab.QMessageBox.warning"
        ) as warning:
            self.tab.run_current_analysis()
            self.wait_for_idle()
        warning.assert_called_once()
        self.assertEqual(self.tab.analysis_progress_bar.text(), "ANALYSIS ERROR")
        self.assertEqual(self.tab.analysis_progress_bar.value(), 0)
        self.assertIs(self.tab.current_analysis_result, previous)
        self.tab.clear_current_workspace()
        self.assertEqual(self.tab.analysis_progress_bar.text(), "NOT RUN")

    def test_csv_import_load_and_failed_import_reset_busy_state(self):
        source = self.root / "current.csv"
        source.write_text("Trigger time,No1 Average Ch1\n0,0.001\n1,0.002\n", encoding="utf-8")
        self.tab.set_source_file(source)
        with patch("gui.tabs.q_current_tab.QMessageBox.information"):
            self.tab.import_current_file()
            self.assertEqual(self.tab.analysis_progress_bar.format(), "IMPORTING...")
            self.wait_for_idle()
        self.assertEqual(self.tab.analysis_progress_bar.text(), "IMPORTED")
        self.assertEqual(len(self.tab.current_samples), 2)
        self.tab.import_current_file()
        self.wait_for_idle()
        self.assertEqual(self.tab.analysis_progress_bar.text(), "IMPORTED")
        with patch("gui.tabs.q_current_tab.get_samples", side_effect=OSError("read failed")), patch(
            "gui.tabs.q_current_tab.QMessageBox.warning"
        ) as warning:
            self.tab.import_current_file()
            self.wait_for_idle()
        warning.assert_called_once()
        self.assertEqual(self.tab.analysis_progress_bar.text(), "IMPORT FAILED")
        self.tab.set_source_file(self.root / "missing.csv")
        with patch("gui.tabs.q_current_tab.QMessageBox.warning") as warning:
            self.tab.import_current_file()
            self.wait_for_idle()
        warning.assert_called_once()
        self.assertEqual(self.tab.analysis_progress_bar.text(), "IMPORT FAILED")
        self.assertTrue(self.tab.import_button.isEnabled())

    def test_replacement_cancellation_restores_previous_state_and_database(self):
        source = self.root / "current.csv"
        source.write_text("Trigger time,No1 Average Ch1\n0,0.001\n1,0.002\n", encoding="utf-8")
        self.tab.set_source_file(source)
        with patch("gui.tabs.q_current_tab.QMessageBox.information"):
            self.tab.import_current_file()
            self.wait_for_idle()
        database = self.tab.current_database_path
        original = database.read_bytes()
        for response in (QMessageBox.No, QMessageBox.Cancel):
            self.tab._set_analysis_result("PASSED")
            self.tab.set_source_file(source)
            with patch("gui.tabs.q_current_tab.QMessageBox.question", return_value=response):
                self.tab.import_current_file()
                self.wait_for_idle()
            self.assertEqual(self.tab.analysis_progress_bar.text(), "PASSED")
            self.assertEqual(database.read_bytes(), original)
            self.assertTrue(self.tab.import_button.isEnabled())

    def test_xlsx_import_and_sqlite_write_failure(self):
        from openpyxl import Workbook

        source = self.root / "current.xlsx"
        book = Workbook()
        book.active.append(["Trigger time", "No1 Average Ch1"])
        book.active.append([0, 0.001])
        book.active.append([1, 0.002])
        book.save(source)
        book.close()
        self.tab.set_source_file(source)
        with patch("gui.tabs.q_current_tab.QMessageBox.information"):
            self.tab.import_current_file()
            self.wait_for_idle()
        self.assertEqual(self.tab.analysis_progress_bar.text(), "IMPORTED")
        self.assertEqual([sample.current_mA for sample in self.tab.current_samples], [1, 2])
        self.tab.set_source_file(source)
        with patch("gui.tabs.q_current_tab.QMessageBox.question", return_value=QMessageBox.Yes), patch(
            "gui.tabs.q_current_tab.import_dataset", side_effect=OSError("write failed")
        ), patch("gui.tabs.q_current_tab.QMessageBox.warning") as warning:
            self.tab.import_current_file()
            self.wait_for_idle()
        warning.assert_called_once()
        self.assertEqual(self.tab.analysis_progress_bar.text(), "IMPORT FAILED")
        self.assertTrue(self.tab.import_button.isEnabled())

    def test_analysis_completion_and_confirmation_use_gui_thread(self):
        self.load_samples()
        callback_threads = []
        update_chart = self.tab._update_current_chart

        def update(*args):
            callback_threads.append(QThread.currentThread() == self.app.thread())
            return update_chart(*args)

        with patch.object(self.tab, "_update_current_chart", side_effect=update):
            for _ in range(3):
                self.tab.run_current_analysis()
                self.wait_for_idle()
                self.assertEqual(self.tab.analysis_progress_bar.text(), "PASSED")
                self.assertFalse(self.tab._task_runner.running)
                self.assertIsNone(self.tab._task_success)
        self.assertEqual(callback_threads, [True, True, True])

    def test_import_worker_remains_responsive_and_confirmation_is_on_gui_thread(self):
        source = self.root / "current.csv"
        source.write_text("Trigger time,No1 Average Ch1\n0,0.001\n1,0.002\n", encoding="utf-8")
        self.tab.set_source_file(source)
        release = Event()
        worker_threads = []

        def normalize(path):
            worker_threads.append(QThread.currentThread() == self.app.thread())
            if not release.wait(5):
                raise RuntimeError("test did not release import")
            return normalize_current_data(path)

        with patch("gui.tabs.q_current_tab.normalize_current_data", side_effect=normalize), patch(
            "gui.tabs.q_current_tab.QMessageBox.information"
        ):
            try:
                self.tab.import_current_file()
                self.assertFalse(self.tab.import_button.isEnabled())
                self.tab.import_current_file()
                self.tab.set_source_file(self.root / "other.csv")
                self.assertEqual(self.tab.source_file_edit.text(), str(source.resolve()))
                alive = []
                QTimer.singleShot(0, lambda: alive.append(True))
                self.app.processEvents()
                self.assertEqual(alive, [True])
                ThemeManager.fn_set_theme(ThemeType.DARK)
                self.tab.fn_refresh_theme()
                self.assertEqual(self.tab.analysis_progress_bar.format(), "IMPORTING...")
            finally:
                release.set()
                self.wait_for_idle()
        self.assertEqual(worker_threads, [False])

        def decline(*_args):
            self.assertEqual(QThread.currentThread(), self.app.thread())
            return QMessageBox.Cancel

        self.tab.set_source_file(source)
        with patch("gui.tabs.q_current_tab.QMessageBox.question", side_effect=decline) as question:
            self.tab.import_current_file()
            self.wait_for_idle()
        question.assert_called_once()
        self.assertEqual(self.tab.analysis_progress_bar.text(), "IMPORTED")
