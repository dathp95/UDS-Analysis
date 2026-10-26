import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from dataclasses import replace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication, QFileDialog
from core.diagnostic_sequence import DiagnosticStep, DiagnosticTestCase
from core.dll_resource import DllResourceStatus
from gui.controllers.vehicle_controller import VehicleController
from gui.controllers.can_dll_resource_controller import CanDllResourceController
from gui.tabs.vehicle_manager_tab import VehicleManagerTab
from gui.widgets.can_interface.current_test_case_panel import CurrentTestCasePanel
from gui.widgets.can_interface.diagnostic_table_panel import CanDiagnosticTablePanel
from gui.themes.theme_manager import ThemeManager
from gui.themes.theme import ThemeType
from models.ecu import ECU
from models.vehicle import Vehicle
from services.vehicle_service import VehicleService
from tests.dll_fixture import pe_dll


class VehicleDllIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dll = self.root / 'fixture.dll'
        self.dll.write_bytes(pe_dll())
        self.other_dll = self.root / 'other.dll'
        self.other_dll.write_bytes(pe_dll(0x14C))
        self.service = self.fresh_service()
        for name in ('BENCH', 'OTHER'):
            self.service.create_vehicle(Vehicle(name))
            self.service.add_ecu(name, ECU('BCM', '681', '601', resources={'dbc': 'keep.dbc', 'custom': 'keep'}))
            self.service.add_ecu(name, ECU('EPS', '682', '602'))
        controller = VehicleController()
        controller._service = self.service
        with patch.object(VehicleManagerTab, '_create_controller', lambda tab: setattr(tab, '_controller', controller)):
            self.manager = VehicleManagerTab()
        self.addCleanup(self.manager.deleteLater)
        self.manager._on_vehicle_changed('BENCH')
        self.manager._on_ecu_selected('BCM')
        self.panel = CanDiagnosticTablePanel(vehicle_service=self.service)
        self.view = CurrentTestCasePanel()
        self.addCleanup(self.panel.deleteLater)
        self.addCleanup(self.view.deleteLater)
        self.metadata = CanDllResourceController(self.panel, self.view)
        self.case = DiagnosticTestCase(1, 'VIN', '', True, [DiagnosticStep(1, 'VIN', 'BCM', '22 F1 90')])
        self.panel.fn_load_sequence(self.case)
        self.panel.vehicle_selector.fn_set_vehicle('BENCH')
        self.panel._select_row(0)
        self.manager.vehicle_data_changed.connect(lambda _: self.panel.fn_refresh_vehicles(preserve_unchanged=True))

    def fresh_service(self):
        service = VehicleService()
        service._repository.root = self.root / 'vehicles'
        return service

    def save(self, path):
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(path), '')):
            self.manager.ecu_resource.btn_dll.click()
        with patch.object(self.manager, '_show_auto_close_info'):
            self.manager._on_save_clicked()

    def test_browse_save_restart_and_vehicle_ecu_isolation(self):
        original = self.manager._current_ecu
        self.save(self.dll)
        self.assertNotIn('dll', original.resources)
        restarted = self.fresh_service()
        value = restarted.load_vehicle('BENCH').ecus[0]
        self.assertEqual(value.resources['dll'], 'resources/dll/BCM/fixture.dll')
        self.assertEqual((value.request_id, value.response_id), ('681', '601'))
        self.assertEqual(value.resources['dbc'], 'keep.dbc')
        self.assertEqual(value.resources['custom'], 'keep')
        self.assertFalse(restarted.load_vehicle('BENCH').ecus[1].resources.get('dll'))
        self.assertNotIn('dll', restarted.load_vehicle('OTHER').ecus[0].resources)
        other = restarted.load_vehicle('OTHER').ecus[0]
        restarted.save_ecu('OTHER', replace(other, resources={'dll': str(self.other_dll)}))
        self.assertEqual(restarted.resolve_ecu_dll_resource('OTHER', 'BCM').status, DllResourceStatus.ARCH_UNSUPPORTED)
        self.assertEqual(restarted.resolve_ecu_dll_resource('BENCH', 'BCM').path, str(self.root/'vehicles/BENCH/resources/dll/BCM/fixture.dll'))
        controller = VehicleController()
        controller._service = restarted
        self.assertEqual(controller.load_vehicle('BENCH').ecus[0].resources['dll'], 'resources/dll/BCM/fixture.dll')

    def test_saved_metadata_refresh_preserves_runtime_and_transport_change_invalidates(self):
        key = self.panel.step_ids[0]
        self.panel.set_step_result(key, '62 F1 90 01', 'Passed')
        changes = []
        self.panel.vehicle_configuration_changed.connect(lambda: changes.append('transport'))
        self.save(self.dll)
        self.assertEqual(changes, [])
        self.assertEqual(self.metadata.metadata.path, str(self.root/'vehicles/BENCH/resources/dll/BCM/fixture.dll'))
        self.assertEqual(self.manager.ecu_resource.txt_dll.text(), 'resources/dll/BCM/fixture.dll')
        self.assertIn('configured', self.manager.ecu_resource.lbl_dll_status.text())
        self.assertIn('configured', self.view.dll_status.text())
        self.assertEqual(self.panel._runtime[key][:2], ('62 F1 90 01', 'Passed'))
        self.assertNotIn(str(self.root), self.view.dll_status.text() + self.view.dll_status.toolTip())
        ecu = self.service.load_vehicle('BENCH').ecus[0]
        self.service.save_ecu('BENCH', replace(ecu, request_id='683'))
        self.manager.vehicle_data_changed.emit('BENCH')
        self.assertEqual(changes, ['transport'])
        self.assertEqual(self.panel._runtime, {})
        self.panel.fn_load_sequence(self.case)
        self.assertEqual(self.panel._runtime, {})

    def test_invalid_manual_save_and_missing_legacy_paths(self):
        before = self.service.load_vehicle('BENCH').ecus[0]
        self.manager.ecu_resource.txt_dll.setText(str(self.root / 'missing.dll'))
        with patch.object(self.manager._controller, 'save_ecu') as save:
            self.manager._on_save_clicked()
        save.assert_not_called()
        self.assertEqual(self.manager._current_ecu, before)
        with self.assertRaises(ValueError):
            self.service.save_ecu('BENCH', replace(before, resources={'dll': str(self.root / 'missing.dll')}))
        self.assertEqual(self.service.resolve_ecu_dll_resource('BENCH', 'BCM').status, DllResourceStatus.NOT_CONFIGURED)
        # Existing legacy references may be missing; unrelated edits must still save.
        self.service._repository.save_ecu('BENCH', replace(before, resources={'dll': str(self.root / 'moved.dll')}))
        legacy = self.service.load_vehicle('BENCH').ecus[0]
        self.service.save_ecu('BENCH', replace(legacy, aliases=['legacy']))
        self.assertEqual(self.service.resolve_ecu_dll_resource('BENCH', 'BCM').status, DllResourceStatus.MISSING)
        for vehicle, ecu in (('../outside', 'BCM'), ('BENCH', 'unknown')):
            self.assertEqual(self.service.resolve_ecu_dll_resource(vehicle, ecu).status, DllResourceStatus.CONFIGURATION_ERROR)

    def test_theme_refresh_is_read_only_and_0x27_remains_disabled(self):
        self.save(self.dll)
        before = self.service.load_vehicle('BENCH')
        theme = ThemeManager.fn_theme()
        self.addCleanup(ThemeManager.fn_set_theme, theme)
        for value in (ThemeType.DARK, ThemeType.LIGHT, ThemeType.DARK):
            ThemeManager.fn_set_theme(value)
            self.manager.fn_refresh_theme()
            self.panel.fn_refresh_theme()
            self.view.fn_refresh_theme()
        self.assertEqual(self.service.load_vehicle('BENCH'), before)
        self.panel.table.item(0, self.panel.COL_REQUEST).setText('27 01')
        self.assertFalse(self.panel.table.cellWidget(0, self.panel.COL_SEND).isEnabled())
        self.assertEqual(self.service.load_vehicle('BENCH'), before)

    def test_can_tab_receives_vehicle_manager_save_event_without_resetting_results(self):
        from PySide6.QtWidgets import QWidget, QVBoxLayout
        from gui.tabs.can_interface_tab import CANInterfaceTab
        from repositories.can_interface_ui_store import CanInterfaceUiStore
        from repositories.can_sequence_repository import CanSequenceRepository
        from tests.gui.test_can_interface_tab import FakeCANService
        window = QWidget()
        window.vehicle_manager_tab = self.manager
        tab = CANInterfaceTab(FakeCANService(), vehicle_service=self.service,
                              sequence_repository=CanSequenceRepository(self.root / 'sequences'),
                              ui_store=CanInterfaceUiStore(self.root / 'prefs.ui'))
        QVBoxLayout(window).addWidget(tab)
        self.addCleanup(window.deleteLater)
        self.addCleanup(tab.close)
        window.resize(1366, 768)
        window.show()
        self.app.processEvents()
        panel = tab.sequence_table
        panel.fn_load_sequence(self.case)
        panel.vehicle_selector.fn_set_vehicle('BENCH')
        panel._select_row(0)
        key = panel.step_ids[0]
        panel.set_step_result(key, '62 F1 90 01', 'Passed')
        generation = tab.diagnostic_controller.generation
        self.save(self.dll)
        self.assertEqual(tab.dll_resource_controller.metadata.path, str(self.root/'vehicles/BENCH/resources/dll/BCM/fixture.dll'))
        self.assertEqual(panel._runtime[key][:2], ('62 F1 90 01', 'Passed'))
        self.assertEqual(tab.diagnostic_controller.generation, generation)
        window.hide()

    def test_unchanged_legacy_is_not_imported_until_explicit_browse_even_same_path(self):
        ecu=self.service.load_vehicle('BENCH').ecus[0]
        self.service._repository.save_ecu('BENCH',replace(ecu,resources={'dll':str(self.dll)}))
        self.manager._reload_current_vehicle(selected_ecu_name='BCM')
        with patch.object(self.manager,'_show_auto_close_info'):
            self.manager._on_save_clicked()
        self.assertEqual(self.service.load_vehicle('BENCH').ecus[0].resources['dll'],str(self.dll))
        self.assertFalse((self.root/'vehicles/BENCH/resources').exists())
        with patch.object(QFileDialog,'getOpenFileName',return_value=(str(self.dll),'')):
            self.manager.ecu_resource.btn_dll.click()
        self.assertFalse((self.root/'vehicles/BENCH/resources').exists())
        with patch.object(self.manager,'_show_auto_close_info'):
            self.manager._on_save_clicked()
        self.assertEqual(self.service.load_vehicle('BENCH').ecus[0].resources['dll'],'resources/dll/BCM/fixture.dll')

    def test_gui_rename_and_delete_move_owned_reference_without_orphans(self):
        from PySide6.QtWidgets import QMessageBox
        self.save(self.dll)
        old=Path(self.metadata.metadata.path)
        self.manager.ecu_info.txt_name.setText('BCM_NEW')
        with patch.object(self.manager,'_show_auto_close_info'):
            self.manager._on_save_clicked()
        value=self.service.resolve_ecu_dll_resource('BENCH','BCM_NEW')
        self.assertTrue(value.configurable)
        self.assertFalse(old.exists())
        self.assertIn('resources/dll/BCM_NEW/',self.manager.ecu_resource.txt_dll.text())
        self.assertNotIn('BCM',[ecu.name for ecu in self.service.load_vehicle('BENCH').ecus])
        with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes):
            self.manager._on_delete_ecu_clicked()
        self.assertFalse(Path(value.path).exists())

    def test_failed_gui_import_preserves_saved_state_results_and_signal(self):
        from PySide6.QtWidgets import QMessageBox
        self.save(self.dll)
        before=self.service.load_vehicle('BENCH')
        key=self.panel.step_ids[0];self.panel.set_step_result(key,'62 F1 90','Passed')
        self.dll.write_bytes(pe_dll(export=b'Changed'))
        with patch.object(QFileDialog,'getOpenFileName',return_value=(str(self.dll),'')):
            self.manager.ecu_resource.btn_dll.click()
        signals=[];self.manager.vehicle_data_changed.connect(signals.append)
        with patch('repositories.vehicle_dll_storage.copy_stream',side_effect=OSError('full')), \
             patch.object(QMessageBox,'warning') as warning:
            self.manager._on_save_clicked()
        warning.assert_called_once()
        self.assertEqual(signals,[])
        self.assertEqual(self.service.load_vehicle('BENCH'),before)
        self.assertEqual(self.panel._runtime[key][1],'Passed')

    def test_vf5np_and_vf6_browse_save_use_separate_copies(self):
        source=self.root/'BCM.dll';source.write_bytes(pe_dll(0x14C))
        for name in ('VF5NP','VF6'):
            self.service.create_vehicle(Vehicle(name))
            self.service.add_ecu(name,ECU('BCM','681','601'))
            self.manager._on_vehicle_changed(name)
            self.save(source)
            self.assertEqual(self.service.load_vehicle(name).ecus[0].resources['dll'],'resources/dll/BCM/BCM.dll')
        first=Path(self.service.resolve_ecu_dll_resource('VF5NP','BCM').path)
        second=Path(self.service.resolve_ecu_dll_resource('VF6','BCM').path)
        self.assertNotEqual(first,second)
        self.assertEqual(first.read_bytes(),second.read_bytes())
        self.manager._on_vehicle_changed('VF5NP')
        source.write_bytes(pe_dll(export=b'Changed'));self.save(source)
        self.assertEqual(second.read_bytes(),pe_dll(0x14C))
