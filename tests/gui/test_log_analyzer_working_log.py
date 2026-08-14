import os
import sys
import types
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPlainTextEdit


class LogAnalyzerWorkingLogTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_action_panel_shows_selected_quick_filter_details(self):
        from gui.widgets.log_analyzer.action_panel import ActionPanel

        panel = ActionPanel()
        self.addCleanup(panel.deleteLater)

        self.assertIsInstance(panel.txt_working_log, QPlainTextEdit)
        self.assertTrue(panel.txt_working_log.isReadOnly())

        panel.fn_set_quick_filter_log(
            {
                "name": "Filter 22 F1 90",
                "filters": {
                    "ecu": "MHU",
                    "request": "22 F1 90",
                    "response": "62 F1 90",
                },
            }
        )

        self.assertEqual(
            panel.txt_working_log.toPlainText(),
            "Name: Filter 22 F1 90\n"
            "ECU: MHU\n"
            "Request: 22 F1 90\n"
            "Response: 62 F1 90",
        )

    def test_right_panel_gives_remaining_height_to_working_log(self):
        from gui.widgets.log_analyzer.right_panel import RightPanel

        panel = RightPanel()
        self.addCleanup(panel.deleteLater)

        right_layout = panel.layout()
        action_layout = panel.action_panel.layout()
        working_log_index = action_layout.indexOf(
            panel.action_panel.txt_working_log
        )

        self.assertEqual(right_layout.count(), 1)
        self.assertIs(right_layout.itemAt(0).widget(), panel.action_panel)
        self.assertEqual(right_layout.stretch(0), 1)
        self.assertGreaterEqual(working_log_index, 0)
        self.assertEqual(action_layout.stretch(working_log_index), 1)

    def test_log_analyzer_replaces_working_log_when_quick_filter_changes(self):
        with patch.dict(
            sys.modules,
            {
                "can": types.SimpleNamespace(),
                "pandas": types.SimpleNamespace(),
            },
        ):
            from gui.tabs.log_analyzer_tab import LogAnalyzerTab

            tab = LogAnalyzerTab()

        self.addCleanup(tab.deleteLater)
        self.addCleanup(self._clear_imported_gui_modules)

        tab.fn_quick_filter(
            {
                "name": "Filter 1",
                "filters": {
                    "ecu": "ECU1",
                    "request": "22 F1 90",
                    "response": "62 F1 90",
                },
            }
        )
        tab.fn_quick_filter(
            {
                "name": "Filter 2",
                "filters": {
                    "ecu": "ECU2",
                    "request": "22 F1 91",
                    "response": "62 F1 91",
                },
            }
        )

        working_log = tab.right_panel.action_panel.txt_working_log.toPlainText()

        self.assertIn("Name: Filter 2", working_log)
        self.assertIn("ECU: ECU2", working_log)
        self.assertIn("Request: 22 F1 91", working_log)
        self.assertIn("Response: 62 F1 91", working_log)
        self.assertNotIn("Filter 1", working_log)
        self.assertNotIn("ECU1", working_log)

        tab.fn_clear_clicked()

        self.assertEqual(
            tab.right_panel.action_panel.txt_working_log.toPlainText(),
            "",
        )

    @staticmethod
    def _clear_imported_gui_modules():
        modules_to_clear = {
            "core.convert_blf",
            "core.export_transactions",
            "core.pipeline",
            "core.report_export",
            "gui.controllers.analysis_controller",
            "gui.controllers.report_controller",
            "gui.tabs.log_analyzer_tab",
        }
        for module_name in modules_to_clear:
            sys.modules.pop(module_name, None)


if __name__ == "__main__":
    unittest.main()
