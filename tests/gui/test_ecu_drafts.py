import unittest
from pathlib import Path
from unittest.mock import patch
from PySide6.QtWidgets import QFileDialog, QMessageBox
from tests.gui import test_vehicle_dll_integration as fixtures


class EcuDraftTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.VehicleDllIntegrationTests.setUpClass.__func__)
    setUp = fixtures.VehicleDllIntegrationTests.setUp
    fresh_service = fixtures.VehicleDllIntegrationTests.fresh_service

    def browse(self, path):
        with patch.object(QFileDialog,'getOpenFileName',return_value=(str(path),'')):
            self.manager.ecu_resource.btn_dll.click()

    def test_eps_browse_bcm_eps_save_uses_retained_draft_and_import_intent(self):
        manager=self.manager
        manager._on_ecu_selected('EPS')
        original=manager._current_ecu
        self.browse(self.dll)
        manager.ecu_info.txt_request.setText('690')
        manager._on_ecu_selected('BCM');manager._on_ecu_selected('EPS')
        self.assertEqual(manager.ecu_resource.txt_dll.text(),str(self.dll))
        self.assertEqual(manager.ecu_info.txt_request.text(),'690')
        self.assertEqual(manager.ecu_resource._browsed_dll,str(self.dll))
        self.assertFalse((self.root/'vehicles/BENCH/resources').exists())
        self.assertFalse(original.resources.get('dll'))
        with patch.object(manager,'_show_auto_close_info'):
            manager._on_save_clicked()
        saved=self.service.load_vehicle('BENCH').ecus[1]
        self.assertEqual(saved.resources['dll'],'resources/dll/EPS/fixture.dll')
        self.assertEqual(saved.request_id,'690')
        self.assertNotIn(('BENCH','EPS'),manager.ecu_drafts.drafts)

    def test_per_vehicle_multiple_drafts_discard_and_theme(self):
        from gui.themes.theme_manager import ThemeManager
        from gui.themes.theme import ThemeType
        manager=self.manager
        manager._on_ecu_selected('EPS');self.browse(self.dll)
        manager._on_ecu_selected('BCM');manager.ecu_info.txt_response.setText('650')
        manager._on_vehicle_changed('OTHER');manager._on_ecu_selected('EPS');self.browse(self.other_dll)
        manager._on_vehicle_changed('BENCH');manager._on_ecu_selected('EPS')
        self.assertEqual(manager.ecu_resource.txt_dll.text(),str(self.dll))
        theme=ThemeManager.fn_theme();self.addCleanup(ThemeManager.fn_set_theme,theme)
        for value in (ThemeType.DARK,ThemeType.LIGHT):
            ThemeManager.fn_set_theme(value);manager.fn_refresh_theme()
        manager.ecu_drafts.discard('BENCH','EPS')
        self.assertEqual(manager.ecu_resource.txt_dll.text(),'')
        self.assertIn(('BENCH','BCM'),manager.ecu_drafts.drafts)
        manager._on_vehicle_changed('OTHER');manager._on_ecu_selected('EPS')
        self.assertEqual(manager.ecu_resource.txt_dll.text(),str(self.other_dll))
        manager.ecu_list.draft_discard_requested.emit('BENCH','BCM')
        self.assertNotIn(('BENCH','BCM'),manager.ecu_drafts.drafts)
        self.assertIn(('OTHER','EPS'),manager.ecu_drafts.drafts)
        self.assertNotIn('dll',self.service.load_vehicle('BENCH').ecus[0].resources)

    def test_failed_save_retains_draft_and_canonical_selection(self):
        manager=self.manager
        manager._on_ecu_selected('EPS');self.browse(self.dll)
        with patch('repositories.vehicle_dll_storage.copy_stream',side_effect=OSError('full')),patch.object(QMessageBox,'warning'):
            manager._on_save_clicked()
        manager._on_ecu_selected('BCM');manager._on_ecu_selected('EPS')
        self.assertEqual(manager.ecu_resource.txt_dll.text(),str(self.dll))
        manager.ecu_list.fn_select_ecu('EPS')
        self.assertEqual(manager.ecu_list.fn_current_ecu_name(),'EPS')
        self.assertIn(('BENCH','EPS'),manager.ecu_drafts.drafts)
