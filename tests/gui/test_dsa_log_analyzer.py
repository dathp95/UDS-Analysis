import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gui.tabs.log_analyzer_tab import LogAnalyzerTab
from models.ecu import ECU
from models.vehicle import Vehicle
from tests.core.test_dsa_txt_parser import HEADER, dsa_frame


class DSALogAnalyzerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2])
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "input.txt"
        self.tab = LogAnalyzerTab()
        self.info = patch("gui.tabs.log_analyzer_tab.QMessageBox.information").start()
        self.warning = patch("gui.tabs.log_analyzer_tab.QMessageBox.warning").start()
        self.addCleanup(patch.stopall)
        self.addCleanup(self.tab.deleteLater)
        self.tab._current_vehicle = Vehicle(
            name="Test", ecus=[ECU(name="ECU", request_id="682", response_id="602")],
        )

    def wait_for(self, predicate):
        deadline = time.monotonic() + 5
        while not predicate() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.005)
        self.assertTrue(predicate(), "Qt background worker did not finish")

    def load(self, content):
        self.path.write_text(content, encoding="utf-8")
        self.tab.log_selector.set_path(str(self.path))
        self.tab.fn_log_file_changed(str(self.path))
        self.wait_for(lambda: self.tab._log_channel_thread is None)

    def test_picker_supports_txt_and_channel_zero_analyzes_in_background(self):
        self.assertEqual(self.tab.log_selector.file_filter, "Log Files (*.blf *.asc *.txt)")
        self.path.write_text(HEADER + dsa_frame(can_id="682", data="02 10 03 AA AA AA AA AA")
                             + dsa_frame(timestamp="00:00:21.098.604", data="06 50 03 00 32 00 C8 CC"), encoding="utf-8")
        with patch("gui.widgets.log_analyzer.path_selector.QFileDialog.getOpenFileName",
                   return_value=(str(self.path), "Log Files (*.blf *.asc *.txt)")) as dialog:
            self.tab.log_selector.browse_button.click()
        self.assertEqual(dialog.call_args.args[-1], "Log Files (*.blf *.asc *.txt)")
        self.wait_for(lambda: self.tab._log_channel_thread is None)
        self.assertEqual(self.tab.channel_selector.fn_channel(), 0)
        self.assertEqual(self.tab.channel_selector.cmb_channel.currentText(), "Channel 0")
        self.assertTrue(self.tab.right_panel.action_panel.btn_run.isEnabled())
        self.tab.fn_run_clicked()
        self.wait_for(lambda: self.tab._analysis_thread is None)
        self.warning.assert_not_called()
        self.assertEqual(self.tab.tbl_result.rowCount(), 1)
        self.assertEqual(self.tab.tbl_result.fn_row_data(0)["Request"], "10 03")
        self.assertEqual(self.tab.tbl_result.fn_row_data(0)["Response"], "50 03 00 32 00 C8")
        self.assertTrue(self.tab.right_panel.action_panel.btn_export.isEnabled())

    def test_multiple_channels_require_selection_and_new_file_clears_stale_state(self):
        style = self.tab.channel_selector.cmb_channel.styleSheet()
        self.load(HEADER + "".join(dsa_frame(channel=ch) for ch in (0, 1, 3)))
        selector = self.tab.channel_selector
        self.assertIsNone(selector.fn_channel())
        self.assertFalse(self.tab.right_panel.action_panel.btn_run.isEnabled())
        self.assertEqual([selector.cmb_channel.itemData(i) for i in range(3)], [0, 1, 3])
        selector.cmb_channel.setCurrentIndex(0)
        self.assertEqual(selector.fn_channel(), 0)
        self.assertTrue(self.tab.right_panel.action_panel.btn_run.isEnabled())
        self.tab.analysis_controller.pipeline_result = {"transactions": []}
        self.path.write_text(HEADER + dsa_frame(channel=3), encoding="utf-8")
        self.tab.fn_log_file_changed(str(self.path))
        self.assertIsNone(selector.fn_channel())
        self.assertIsNone(self.tab.analysis_controller.pipeline_result)
        self.wait_for(lambda: self.tab._log_channel_thread is None)
        self.assertEqual(selector.fn_channel(), 3)
        self.assertEqual(selector.cmb_channel.styleSheet(), style)

    def test_unsupported_txt_warns_and_keeps_analyze_disabled(self):
        self.load("A different TXT log format\n")
        self.warning.assert_called_once()
        self.assertIn("Unsupported TXT", self.warning.call_args.args[2])
        self.assertIsNone(self.tab.channel_selector.fn_channel())
        self.assertFalse(self.tab.right_panel.action_panel.btn_run.isEnabled())
        self.assertIsNone(self.tab.analysis_controller.pipeline_result)

    def test_diagnostics_are_visible_after_discovery_and_analysis_with_nonblocking_warning(self):
        content = (HEADER + dsa_frame(can_id="682", data="02 10 03 AA AA AA AA AA")
                   + dsa_frame(timestamp="00:00:21.098.604", data="06 50 03 00 32 00 C8 CC")
                   + dsa_frame(channel=3) + dsa_frame(dlc=7) + dsa_frame(frame_type="29n"))
        with self.assertLogs("core.log_parsers.dsa_txt_parser", level="WARNING"):
            self.load(content)
        panel = self.tab.right_panel.action_panel
        self.assertIn("warnings", panel.lbl_analysis_status.text().lower())
        self.assertFalse(panel.lbl_parser_diagnostics.isHidden())
        self.assertIn("Malformed: 1", panel.lbl_parser_diagnostics.text())
        self.assertIn("Unsupported: 1", panel.lbl_parser_diagnostics.text())
        self.warning.assert_not_called()
        self.info.assert_not_called()
        self.tab.channel_selector.cmb_channel.setCurrentIndex(0)
        self.assertIn("Channel 0: 2", panel.lbl_parser_diagnostics.text())
        with self.assertLogs("core.log_parsers.dsa_txt_parser", level="WARNING"):
            self.tab.fn_run_clicked()
            self.wait_for(lambda: self.tab._analysis_thread is None)
        self.assertEqual(panel.lbl_analysis_status.text(), "Completed with warnings")
        self.assertEqual(self.tab.analysis_controller.pipeline_result["parser_diagnostics"].pipeline_frames, 2)
        self.assertIn("incomplete", panel.lbl_parser_diagnostics.text().lower())
        self.assertIn("Frames supplied to UDS: 2", panel.lbl_parser_diagnostics.toolTip())
        self.tab.fn_log_file_changed("")
        self.assertTrue(panel.lbl_parser_diagnostics.isHidden())

    def test_no_valid_frames_prevents_analyze_and_clears_diagnostics(self):
        with self.assertLogs("core.log_parsers.dsa_txt_parser", level="WARNING"):
            self.load(HEADER + dsa_frame(dlc=7) + dsa_frame(frame_type="29n"))
        self.assertFalse(self.tab.right_panel.action_panel.btn_run.isEnabled())
        self.assertIsNone(self.tab.channel_selector.fn_channel())
        self.assertTrue(self.tab.right_panel.action_panel.lbl_parser_diagnostics.isHidden())
        self.warning.assert_called_once()

    def test_parser_summary_preserves_theme_and_is_removed_for_other_formats(self):
        from gui.themes.theme import ThemeType
        from gui.themes.theme_manager import ThemeManager
        with self.assertLogs("core.log_parsers.dsa_txt_parser", level="WARNING"):
            self.load(HEADER + dsa_frame() + dsa_frame(dlc=7))
        panel = self.tab.right_panel.action_panel
        original_theme = ThemeManager.fn_theme()
        try:
            for theme in (ThemeType.LIGHT, ThemeType.DARK):
                ThemeManager.fn_set_theme(theme)
                self.tab.fn_refresh_theme()
                self.assertIn(ThemeManager.fn_colors().WARNING, panel.lbl_parser_diagnostics.styleSheet())
                self.assertTrue(panel.lbl_parser_diagnostics.wordWrap())
        finally:
            ThemeManager.fn_set_theme(original_theme)
        asc = self.path.with_suffix(".asc")
        asc.write_text("0.001 1 682 Rx d 8 02 10 03 AA AA AA AA AA\n", encoding="utf-8")
        self.tab.log_selector.set_path(str(asc))
        self.tab.fn_log_file_changed(str(asc))
        self.wait_for(lambda: self.tab._log_channel_thread is None)
        self.assertTrue(panel.lbl_parser_diagnostics.isHidden())
        self.assertEqual(panel.lbl_analysis_status.text(), "Log loaded")


if __name__ == "__main__":
    unittest.main()
