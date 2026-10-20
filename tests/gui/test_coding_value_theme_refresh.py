import copy
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget

from core.coding_value import CodingValueOption, CodingValueRow
from core.coding_value_workspace import CodingEcuWorkspace
from core.coding_value_workspace_store import CodingWorkspaceStore
from gui.tabs.coding_value_tab import CodingValueTab
from gui.tabs.log_analyzer_tab import LogAnalyzerTab
from gui.tabs.vehicle_manager_tab import VehicleManagerTab
from gui.themes.theme import ThemeType
from gui.themes.theme_manager import ThemeManager
from gui.widgets.coding_value.coding_value_table import CodingValueTable
from gui.widgets.controls.theme_switch import ThemeSwitch
from gui.windows.main_window import MainWindow


ROW = CodingValueRow(parameter="Byte 14 nibble", byte_pos="14", bit_pos="0",
                     bit_length="4", raw_value="", decoded_value="", decoded_options=(
                         CodingValueOption("0", "Off"), CodingValueOption("F", "On")))


class ThemeWindow(MainWindow):
    """Use the real shortcut/theme methods without application startup or activation."""
    def __init__(self, store):
        QMainWindow.__init__(self)
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)
        self.log_analyzer_tab = LogAnalyzerTab()
        self.coding_value_tab = CodingValueTab(workspace_store=store)
        self.tabs.addTab(self.log_analyzer_tab, "Log Analyzer")
        self.tabs.addTab(self.coding_value_tab, "Coding Value")
        self.vehicle_manager_tab = QWidget(self)
        self.vehicle_manager_tab.theme_switch = ThemeSwitch(self.vehicle_manager_tab)
        self.vehicle_manager_tab.theme_switch.fn_set_theme(ThemeManager.fn_theme())
        self.vehicle_manager_tab.theme_switch.theme_changed.connect(
            lambda theme: VehicleManagerTab.fn_change_theme(self.vehicle_manager_tab, theme))
        for name in ("crc_converter_tab", "can_interface_tab", "q_current_tab", "license_support_tab"):
            setattr(self, name, QWidget(self))
        with patch("gui.windows.main_window.load_shortcuts", return_value=[
                {"key": "Ctrl+B", "action": "toggle_theme"}]):
            self._setup_shortcuts()


class CodingValueThemeRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.addCleanup(ThemeManager.fn_set_theme, ThemeManager.fn_theme())
        ThemeManager.fn_set_theme(ThemeType.LIGHT)

    def table(self, raw="FF"):
        table = CodingValueTable()
        self.addCleanup(table.deleteLater)
        table.set_rows([ROW])
        # Reproduce an already-loaded invalid value, not a user edit. Preserve
        # it verbatim: theme changes must never normalize or repair this state.
        with QSignalBlocker(table):
            table.item(0, 4).setText(raw)
        table._row_state[0]["last_raw"] = raw
        table._row_state[0]["original_raw"] = raw
        table.apply_check_results()
        return table

    def snapshot(self, table):
        return (tuple(tuple(table.item(r, c).text() if table.item(r, c) else None
                            for c in range(table.columnCount())) for r in range(table.rowCount())),
                copy.deepcopy(table._row_state),
                tuple((table.cellWidget(r, 5).currentIndex(), table.cellWidget(r, 5).currentText())
                      for r in range(table.rowCount())))

    def test_invalid_byte14_never_validates_or_changes_during_theme_refresh(self):
        table = self.table()
        before = self.snapshot(table)
        item_events, raw_events = [], []
        table.itemChanged.connect(lambda item: item_events.append(item.column()))
        table.raw_value_changed.connect(lambda *args: raw_events.append(args))
        with patch.object(table, "_apply_raw_value_to_row", wraps=table._apply_raw_value_to_row) as validate, \
             patch("gui.widgets.coding_value.coding_value_table.QMessageBox.warning") as warning:
            for theme in (ThemeType.DARK, ThemeType.LIGHT) * 3:
                ThemeManager.fn_set_theme(theme)
                table.fn_refresh_theme()
                self.assertEqual(self.snapshot(table), before)
                self.assertEqual(table.item(0, 8).background().color().name(),
                                 ThemeManager.fn_colors().SUCCESS.lower())
        validate.assert_not_called()
        warning.assert_not_called()
        self.assertEqual(item_events, [])
        self.assertEqual(raw_events, [])

    def test_valid_and_empty_values_do_not_emit_data_changes_on_theme_refresh(self):
        for raw in ("0F", ""):
            with self.subTest(raw=raw):
                table = self.table(raw)
                before = self.snapshot(table)
                changes = []
                table.raw_value_changed.connect(lambda *args: changes.append(args))
                with patch("gui.widgets.coding_value.coding_value_table.QMessageBox.warning") as warning:
                    for theme in (ThemeType.DARK, ThemeType.LIGHT):
                        ThemeManager.fn_set_theme(theme)
                        table.fn_refresh_theme()
                warning.assert_not_called()
                self.assertEqual(changes, [])
                self.assertEqual(self.snapshot(table), before)

    def test_user_edit_still_validates_once_after_repeated_theme_changes(self):
        table = self.table("0F")
        with patch("gui.widgets.coding_value.coding_value_table.QMessageBox.warning") as warning:
            for theme in (ThemeType.DARK, ThemeType.LIGHT) * 2:
                ThemeManager.fn_set_theme(theme)
                table.fn_refresh_theme()
            warning.assert_not_called()
            changes = []
            table.raw_value_changed.connect(lambda *args: changes.append(args))
            table.item(0, 4).setText("0A")
            self.assertEqual(table.item(0, 4).text(), "0A")
            self.assertEqual(len(changes), 1)
            table.item(0, 4).setText("10")
            warning.assert_called_once()
            self.assertEqual(warning.call_args.args[1], "Invalid Raw Value")
            self.assertIn("Byte 14", warning.call_args.args[2])
            self.assertIn("BitLength 4", warning.call_args.args[2])
            self.assertEqual(table.item(0, 4).text(), "0A")
            self.assertEqual(len(changes), 1)

    def test_no_match_result_keeps_data_and_updates_theme_colors(self):
        table = self.table("0F")
        table._row_state[0]["original_raw"] = "00"
        table.apply_check_results()
        before = self.snapshot(table)
        for theme in (ThemeType.DARK, ThemeType.LIGHT):
            ThemeManager.fn_set_theme(theme)
            with patch("gui.widgets.coding_value.coding_value_table.QMessageBox.warning") as warning:
                table.fn_refresh_theme()
            warning.assert_not_called()
            self.assertEqual(self.snapshot(table), before)
            self.assertEqual(table.item(0, 8).text(), "No-M")
            self.assertEqual(table.item(0, 8).background().color().name(),
                             ThemeManager.fn_colors().WARNING.lower())

    def test_signal_block_state_restored_even_if_child_refresh_fails(self):
        table = self.table("0F")
        for blocked in (False, True):
            table.blockSignals(blocked)
            combo = table.cellWidget(0, 5)
            combo.blockSignals(blocked)
            with patch.object(combo, "fn_refresh_theme", side_effect=RuntimeError("style error")):
                with self.assertRaisesRegex(RuntimeError, "style error"):
                    table.fn_refresh_theme()
            self.assertEqual(table.signalsBlocked(), blocked)
            self.assertEqual(combo.signalsBlocked(), blocked)

    def test_ctrl_b_from_both_tabs_keeps_all_workspace_datasets_unchanged(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
            store = CodingWorkspaceStore(Path(directory) / "workspaces.json")
            window = ThemeWindow(store)
            self.addCleanup(window.deleteLater)
            window.resize(1200, 800)
            window.show()
            window.activateWindow()
            tab = window.coding_value_tab
            tab.workspace_sidebar.add_workspace(CodingEcuWorkspace.create("Second"), select=False)
            panels = list(tab._panel_by_workspace_id.values())
            for panel in panels:
                panel.table.set_rows([ROW])
                with QSignalBlocker(panel.table):
                    panel.table.item(0, 4).setText("FF")
                panel.table._row_state[0].update(last_raw="FF", original_raw="FF")
                panel.txt_coding_value.setPlainText("00 " * 14 + "FF")
                panel.table.apply_check_results()
            before = [(self.snapshot(p.table), p.create_workspace_snapshot()) for p in panels]
            files_before = {p.relative_to(directory): p.read_bytes()
                            for p in Path(directory).rglob("*") if p.is_file()}
            state_events = []
            for panel in panels:
                panel.state_changed.connect(lambda: state_events.append("changed"))
            with patch("gui.widgets.coding_value.coding_value_table.QMessageBox.warning") as warning:
                for active in (window.log_analyzer_tab, tab):
                    window.tabs.setCurrentWidget(active)
                    self.application.processEvents()
                    for _ in range(4):
                        previous_theme = ThemeManager.fn_theme()
                        QTest.keyClick(window, Qt.Key_B, Qt.ControlModifier)
                        self.application.processEvents()
                        self.assertNotEqual(ThemeManager.fn_theme(), previous_theme)
                        self.assertEqual([(self.snapshot(p.table), p.create_workspace_snapshot())
                                          for p in panels], before)
                warning.assert_not_called()
            self.assertEqual(state_events, [])
            self.assertEqual({p.relative_to(directory): p.read_bytes()
                              for p in Path(directory).rglob("*") if p.is_file()}, files_before)
            window.close()


if __name__ == "__main__":
    unittest.main()
