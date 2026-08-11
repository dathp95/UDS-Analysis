import os
import sys
import types
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication


class MainWindowShortcutTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_shortcuts_only_run_on_log_analyzer_tab(self):
        with patch.dict(
            sys.modules,
            {
                "can": types.SimpleNamespace(),
                "pandas": types.SimpleNamespace(),
            },
        ):
            from gui.windows.main_window import MainWindow

            with patch("gui.windows.main_window.load_shortcuts", return_value=[]):
                window = MainWindow()

        self.addCleanup(window.deleteLater)
        self.addCleanup(self._clear_imported_gui_modules)

        action = Mock()

        window.tabs.setCurrentWidget(window.vehicle_manager_tab)
        window._run_log_analyzer_shortcut(action)

        action.assert_not_called()

        window.tabs.setCurrentWidget(window.log_analyzer_tab)
        window._run_log_analyzer_shortcut(action)

        action.assert_called_once_with()

    def test_coding_value_tab_is_next_to_log_analyzer(self):
        with patch.dict(
            sys.modules,
            {
                "can": types.SimpleNamespace(),
                "pandas": types.SimpleNamespace(),
            },
        ):
            from gui.windows.main_window import MainWindow

            with patch("gui.windows.main_window.load_shortcuts", return_value=[]):
                window = MainWindow()

        self.addCleanup(window.deleteLater)
        self.addCleanup(self._clear_imported_gui_modules)

        self.assertIs(window.tabs.widget(0), window.log_analyzer_tab)
        self.assertIs(window.tabs.widget(1), window.coding_value_tab)
        self.assertEqual(window.tabs.tabText(1), "Coding value")
        self.assertIs(window.tabs.widget(2), window.vehicle_manager_tab)

    @staticmethod
    def _clear_imported_gui_modules():
        modules_to_clear = {
            "core.convert_blf",
            "core.export_transactions",
            "core.pipeline",
            "core.report_export",
            "gui.controllers.analysis_controller",
            "gui.controllers.report_controller",
            "gui.tabs.coding_value_tab",
            "gui.tabs.log_analyzer_tab",
            "gui.windows.main_window",
        }
        for module_name in modules_to_clear:
            sys.modules.pop(module_name, None)
