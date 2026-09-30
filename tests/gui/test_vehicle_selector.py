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
from gui.dialogs.export_vehicle_dialog import ExportVehicleDialog
from gui.dialogs.import_display_names_dialog import ImportDisplayNamesDialog
from gui.widgets.controls.cancel_button import CancelButton
from gui.widgets.vehicle_manager.vehicle_selector import VehicleSelectorWidget
from models.ecu import ECU
from models.vehicle import Vehicle


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
        self.assertFalse(tab.btn_export_vehicle.isEnabled())

    def test_vehicle_manager_enables_export_after_vehicle_selection(self):
        tab = VehicleManagerTab()
        self.addCleanup(tab.deleteLater)
        vehicle = Vehicle(
            name="VF3",
            ecus=[
                ECU(
                    name="BCM",
                    request_id="681",
                    response_id="601",
                )
            ],
        )

        with patch.object(
            tab._controller,
            "load_vehicle",
            return_value=vehicle,
        ):
            tab._on_vehicle_changed("VF3")

        self.assertTrue(tab.btn_export_vehicle.isEnabled())

    def test_vehicle_manager_exports_selected_vehicle_ecu_list(self):
        tab = VehicleManagerTab()
        self.addCleanup(tab.deleteLater)
        tab._current_vehicle_name = "VF3"

        with patch.object(
            tab._controller,
            "export_vehicle_ecu_list",
            return_value="BCM|681|601",
        ) as export_list, patch(
            "gui.tabs.vehicle_manager_tab.ExportVehicleDialog"
        ) as dialog:
            tab._on_export_vehicle_clicked()

        export_list.assert_called_once_with("VF3")
        dialog.assert_called_once_with(
            "VF3",
            "BCM|681|601",
            tab,
        )
        dialog.return_value.exec.assert_called_once_with()

    def test_vehicle_manager_save_renamed_ecu_uses_original_name(self):
        tab = VehicleManagerTab()
        self.addCleanup(tab.deleteLater)
        original_ecu = ECU(
            name="BCM",
            request_id="681",
            response_id="601",
        )
        tab._current_vehicle_name = "VF3"
        tab._current_vehicle = Vehicle(
            name="VF3",
            ecus=[original_ecu],
        )
        tab._current_ecu = original_ecu
        tab.ecu_info.fn_set_ecu(original_ecu)
        tab.ecu_info.txt_name.setText("BCM_NEW")

        with patch.object(
            tab._controller,
            "save_ecu",
        ) as save_ecu, patch.object(
            tab._controller,
            "delete_ecu",
        ) as delete_ecu, patch.object(
            tab,
            "_reload_current_vehicle",
        ) as reload_vehicle, patch.object(
            tab,
            "_show_auto_close_info",
        ), patch.object(
            tab,
            "_notify_vehicle_data_changed",
        ):
            tab._on_save_clicked()

        saved_ecu = save_ecu.call_args.args[1]
        self.assertEqual(saved_ecu.name, "BCM_NEW")
        save_ecu.assert_called_once_with(
            "VF3",
            saved_ecu,
            existing_ecu_name="BCM",
        )
        delete_ecu.assert_called_once_with(
            "VF3",
            "BCM",
        )
        reload_vehicle.assert_called_once_with(
            selected_ecu_name="BCM_NEW"
        )

    def test_export_vehicle_dialog_uses_import_ecu_list_format(self):
        dialog = ExportVehicleDialog(
            "VF3",
            "BCM|681|601\nACM|688|608",
        )
        self.addCleanup(dialog.deleteLater)

        self.assertEqual(
            dialog.fn_export_text(),
            "BCM|681|601\nACM|688|608",
        )
        self.assertTrue(dialog.txt_ecus.isReadOnly())

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

    def test_display_rules_dialog_keeps_input_after_invalid_import(self):
        dialog = ImportDisplayNamesDialog()
        self.addCleanup(dialog.deleteLater)
        dialog.txt_rules.setPlainText("22 F1 GG|Broken")

        with patch(
            "gui.dialogs.import_display_names_dialog.QMessageBox.warning"
        ) as warning:
            dialog._on_import_clicked()

        warning.assert_called_once()
        self.assertEqual(dialog.result(), 0)
        self.assertEqual(
            dialog.txt_rules.toPlainText(),
            "22 F1 GG|Broken",
        )


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

    def test_analyze_waits_for_vehicle_after_selecting_valid_log(self):
        log_file = self._write_log(
            "0.001 1 681 Rx d 8 03 22 F1 90 00 00 00 00\n"
        )
        self.tab.log_selector.set_path(str(log_file))
        self.tab.fn_log_file_changed(str(log_file))

        self.assertEqual(self.tab.channel_selector.fn_channel(), 1)
        self.assertFalse(self.tab.right_panel.action_panel.btn_run.isEnabled())

    def test_multi_channel_log_requires_channel_selection(self):
        log_file = self._write_log(
            "0.001 2 681 Rx d 8 03 22 F1 90 00 00 00 00\n"
            "0.002 1 682 Rx d 8 03 22 F1 91 00 00 00 00\n"
        )
        self.tab._current_vehicle = object()
        self.tab.log_selector.set_path(str(log_file))
        self.tab.fn_log_file_changed(str(log_file))

        self.assertTrue(self.tab.channel_selector.cmb_channel.isEnabled())
        self.assertEqual(self.tab.channel_selector.cmb_channel.currentIndex(), -1)
        self.assertIsNone(self.tab.channel_selector.fn_channel())
        self.assertFalse(self.tab.right_panel.action_panel.btn_run.isEnabled())

        self.tab.channel_selector.cmb_channel.setCurrentIndex(0)

        self.assertEqual(self.tab.channel_selector.fn_channel(), 1)
        self.assertTrue(self.tab.right_panel.action_panel.btn_run.isEnabled())

    def test_analyze_passes_selected_channel_to_controller(self):
        log_file = self._write_log(
            "0.001 2 681 Rx d 8 03 22 F1 90 00 00 00 00\n"
        )
        self.tab._current_vehicle = object()
        self.tab.log_selector.set_path(str(log_file))
        self.tab.fn_log_file_changed(str(log_file))

        with patch.object(
            self.tab.analysis_controller,
            "fn_run",
            return_value={"transactions": []},
        ) as run_analysis:
            self.tab.fn_run_clicked()

        run_analysis.assert_called_once_with(
            log_file=str(log_file),
            vehicle=self.tab._current_vehicle,
            channel=2,
        )

    def test_non_sequential_selected_channel_is_passed_as_item_data(self):
        log_file = self._write_log(
            "0.001 2 681 Rx d 8 03 22 F1 90 00 00 00 00\n"
            "0.002 5 682 Rx d 8 03 22 F1 91 00 00 00 00\n"
            "0.003 12 683 Rx d 8 03 22 F1 92 00 00 00 00\n"
        )
        self.tab._current_vehicle = object()
        self.tab.log_selector.set_path(str(log_file))
        self.tab.fn_log_file_changed(str(log_file))
        self.tab.channel_selector.cmb_channel.setCurrentIndex(1)

        with patch.object(
            self.tab.analysis_controller,
            "fn_run",
            return_value={"transactions": []},
        ) as run_analysis:
            self.tab.fn_run_clicked()

        run_analysis.assert_called_once_with(
            log_file=str(log_file),
            vehicle=self.tab._current_vehicle,
            channel=5,
        )

    def test_loading_new_file_clears_previous_channel_selection(self):
        first_log = self._write_log(
            "0.001 1 681 Rx d 8 03 22 F1 90 00 00 00 00\n"
            "0.002 2 682 Rx d 8 03 22 F1 91 00 00 00 00\n"
            "0.003 3 683 Rx d 8 03 22 F1 92 00 00 00 00\n"
        )
        second_log = self._write_log(
            "0.001 4 681 Rx d 8 03 22 F1 90 00 00 00 00\n"
            "0.002 5 682 Rx d 8 03 22 F1 91 00 00 00 00\n"
        )
        self.tab._current_vehicle = object()
        self.tab.log_selector.set_path(str(first_log))
        self.tab.fn_log_file_changed(str(first_log))
        self.tab.channel_selector.cmb_channel.setCurrentIndex(1)
        self.assertEqual(self.tab.channel_selector.fn_channel(), 2)

        self.tab.log_selector.set_path(str(second_log))
        self.tab.fn_log_file_changed(str(second_log))

        self.assertEqual(self.tab.channel_selector.cmb_channel.currentIndex(), -1)
        self.assertIsNone(self.tab.channel_selector.fn_channel())
        self.assertEqual(self.tab.channel_selector.cmb_channel.count(), 2)
        self.assertEqual(
            [
                self.tab.channel_selector.cmb_channel.itemData(index)
                for index in range(self.tab.channel_selector.cmb_channel.count())
            ],
            [4, 5],
        )
        self.assertFalse(self.tab.right_panel.action_panel.btn_run.isEnabled())

    def test_does_not_reject_log_with_multiple_pt_bo_info_markers(self):
        log_file = self._write_log(
            "PT BO INFO\n"
            "PT BO INFO\n"
            "0.001 1 681 Rx d 8 03 22 F1 90 00 00 00 00\n"
        )
        self.tab.log_selector.set_path(str(log_file))

        with patch("gui.tabs.log_analyzer_tab.QMessageBox.warning") as warning:
            self.tab.fn_log_file_changed(str(log_file))

        self.assertEqual(self.tab.log_selector.path(), str(log_file))
        self.assertEqual(self.tab.channel_selector.fn_channel(), 1)
        warning.assert_not_called()
