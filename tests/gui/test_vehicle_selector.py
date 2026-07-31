import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from gui.tabs.log_analyzer_tab import LogAnalyzerTab
from gui.tabs.vehicle_manager_tab import VehicleManagerTab
from gui.dialogs.import_ecu_dialog import ImportECUDialog
from gui.dialogs.import_display_names_dialog import ImportDisplayNamesDialog
from gui.widgets.controls.cancel_button import CancelButton
from gui.widgets.vehicle_manager.vehicle_selector import VehicleSelectorWidget


class VehicleSelectorWidgetTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_can_leave_vehicle_unselected(self):
        selector = VehicleSelectorWidget()

        selector.fn_set_vehicles(
            ["VF3", "VF6"],
            allow_empty_selection=True,
        )

        self.assertEqual(selector.fn_vehicle(), "")

    def test_vehicle_popup_uses_opaque_background(self):
        selector = VehicleSelectorWidget()

        self.assertTrue(
            selector.cmb_vehicle.view().testAttribute(
                Qt.WA_OpaquePaintEvent
            )
        )
        self.assertTrue(
            selector.cmb_vehicle.view().viewport().testAttribute(
                Qt.WA_OpaquePaintEvent
            )
        )
        self.assertTrue(
            selector.cmb_vehicle.view().viewport().testAttribute(
                Qt.WA_StyledBackground
            )
        )
        self.assertIn(
            "QComboBox QAbstractItemView",
            selector.cmb_vehicle.styleSheet(),
        )

    def test_vehicle_manager_has_display_names_import_button(self):
        tab = VehicleManagerTab()
        self.addCleanup(tab.deleteLater)

        self.assertEqual(
            tab.btn_import_display_names.text(),
            "Import Display Names",
        )
        self.assertEqual(
            tab.btn_import_display_rules.text(),
            "Import Display Rules",
        )

    def test_vehicle_manager_starts_without_selected_vehicle_or_ecus(self):
        tab = VehicleManagerTab()
        self.addCleanup(tab.deleteLater)

        self.assertEqual(tab.vehicle_selector.fn_vehicle(), "")
        self.assertEqual(tab.ecu_list.rowCount(), 0)
        self.assertIsNone(tab._current_vehicle)
        self.assertFalse(tab.btn_add_ecu.isEnabled())
        self.assertFalse(tab.btn_import_ecus.isEnabled())

    def test_display_names_import_uses_selected_json_file(self):
        tab = VehicleManagerTab()
        self.addCleanup(tab.deleteLater)

        with patch(
            "gui.tabs.vehicle_manager_tab.QFileDialog.getOpenFileName",
            return_value=("C:/display_names.json", "JSON Files (*.json)"),
        ), patch(
            "gui.tabs.vehicle_manager_tab.import_display_names"
        ) as import_file, patch(
            "gui.tabs.vehicle_manager_tab.reload_display_names"
        ) as reload_names, patch.object(
            tab,
            "_show_auto_close_info",
        ) as show_success:
            tab._on_import_display_names_clicked()

        import_file.assert_called_once_with("C:/display_names.json")
        reload_names.assert_called_once_with()
        show_success.assert_called_once()

    def test_display_rules_import_uses_dialog_rules(self):
        tab = VehicleManagerTab()
        self.addCleanup(tab.deleteLater)

        dialog = patch(
            "gui.tabs.vehicle_manager_tab.ImportDisplayNamesDialog"
        ).start()
        self.addCleanup(patch.stopall)
        dialog.return_value.exec.return_value = 1
        dialog.return_value.fn_rules.return_value = "22 F1 20|Global Time"

        with patch(
            "gui.tabs.vehicle_manager_tab.import_display_name_rules"
        ) as import_rules, patch(
            "gui.tabs.vehicle_manager_tab.reload_display_names"
        ) as reload_names, patch.object(
            tab,
            "_show_auto_close_info",
        ) as show_success:
            tab._on_import_display_rules_clicked()

        import_rules.assert_called_once_with("22 F1 20|Global Time")
        reload_names.assert_called_once_with()
        show_success.assert_called_once()

    def test_import_dialog_cancel_buttons_use_neutral_cancel_control(self):
        ecu_dialog = ImportECUDialog()
        display_dialog = ImportDisplayNamesDialog()
        self.addCleanup(ecu_dialog.deleteLater)
        self.addCleanup(display_dialog.deleteLater)

        self.assertIsInstance(ecu_dialog.btn_cancel, CancelButton)
        self.assertIsInstance(display_dialog.btn_cancel, CancelButton)


class LogAnalyzerTabTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tab = LogAnalyzerTab()

    def tearDown(self):
        self.tab.deleteLater()

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

    def test_starts_without_a_vehicle_selection(self):
        self.assertEqual(self.tab.vehicle_selector.fn_vehicle(), "")

    def test_analyze_requests_vehicle_after_selecting_valid_log(self):
        log_file = self._write_log("PT BO INFO\n")
        self.tab.log_selector.set_path(str(log_file))
        self.tab.fn_log_file_changed(str(log_file))

        self.assertTrue(self.tab.right_panel.action_panel.btn_run.isEnabled())

        with patch("gui.tabs.log_analyzer_tab.QMessageBox.warning") as warning:
            self.tab.fn_run_clicked()

        self.assertIn("Please select a vehicle", warning.call_args.args[2])

    def test_rejects_log_with_multiple_pt_bo_info_markers(self):
        log_file = self._write_log("PT BO INFO\nPT BO INFO\n")
        self.tab.log_selector.set_path(str(log_file))

        with patch("gui.tabs.log_analyzer_tab.QMessageBox.warning") as warning:
            self.tab.fn_log_file_changed(str(log_file))

        self.assertEqual(self.tab.log_selector.path(), "")
        self.assertFalse(self.tab.right_panel.action_panel.btn_run.isEnabled())
        self.assertEqual(warning.call_args.args[1], "Log File Not Supported")
