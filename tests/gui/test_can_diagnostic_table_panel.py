import os
import unittest
from types import SimpleNamespace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from core.diagnostic_sequence import DiagnosticStep, DiagnosticTestCase
from models.vehicle import Vehicle
from models.ecu import ECU


class CanDiagnosticTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def make_panel(self):
        from gui.widgets.can_interface.diagnostic_table_panel import CanDiagnosticTablePanel
        service = SimpleNamespace(list_vehicles=lambda: ['BENCH'], load_vehicle=lambda _: Vehicle('BENCH', ecus=[ECU('TEST')]))
        panel = CanDiagnosticTablePanel(vehicle_service=service)
        self.addCleanup(panel.deleteLater)
        panel.fn_load_sequence(DiagnosticTestCase(1, 'TEST', '', True, [DiagnosticStep(1,'TEST','TEST','22 F1 90')]))
        return panel

    def test_exact_columns_stable_actions_and_independent_checks(self):
        panel = self.make_panel()
        self.assertEqual(panel.HEADERS, ('✓','Step','ECU','Payload (HEX)','>','Delay (ms)','Repeat',
                         'Expected Response (HEX)','Receive Message (HEX)','Results','Comment'))
        self.assertFalse(panel.table.isSortingEnabled())
        original = panel.step_ids[0]
        actions = []
        panel.row_send_requested.connect(actions.append)
        panel.table.cellWidget(0, panel.COL_SEND).click()
        self.assertEqual(actions, [original])
        self.assertEqual(panel.checked_step_ids(), ())
        panel.table.item(0,panel.COL_CHECK).setCheckState(Qt.Checked)
        panel.fn_add_step_after_selected()
        panel.table.selectRow(0)
        panel.fn_remove_selected_step()
        survivor = panel.step_ids[0]
        panel.table.cellWidget(0, panel.COL_SEND).click()
        self.assertEqual(actions[-1], survivor)
        self.assertNotEqual(original, survivor)
        self.assertEqual(panel.table.item(0, panel.COL_RECEIVE).text(), '—')
        self.assertEqual(panel.table.item(0, panel.COL_RESULT).text(), '—')

    def test_validation_comment_and_runtime_separation(self):
        panel = self.make_panel()
        panel.table.item(0,panel.COL_REQUEST).setText('zz')
        self.assertEqual(panel.fn_current_sequence().steps[0].request, '22 F1 90')
        self.assertIn('Invalid', panel.notice.text())
        for column, value in ((panel.COL_DELAY,'-1'), (panel.COL_REPEAT,'0')):
            panel.table.item(0,column).setText(value)
        self.assertEqual(panel.fn_current_sequence().steps[0].delay_ms, 100)
        self.assertEqual(panel.fn_current_sequence().steps[0].repeat, 1)
        panel.table.item(0,panel.COL_COMMENT).setText('Bench only')
        self.assertEqual(panel.fn_current_sequence().steps[0].comment, 'Bench only')
        panel.set_step_result(panel.step_ids[0], '62 F1 90', 'Not Evaluated')
        self.assertEqual(panel.table.item(0,panel.COL_RECEIVE).text(), '62 F1 90')
        self.assertFalse(hasattr(panel.fn_current_sequence().steps[0], 'received_payload'))
        panel.reset_runtime_results()
        self.assertEqual(panel.table.item(0,panel.COL_RESULT).text(),'—')

    def test_vehicle_is_explicit_and_missing_ecu_is_preserved(self):
        panel = self.make_panel()
        self.assertEqual(panel.fn_current_vehicle(), '')
        self.assertIn('Select Vehicle', panel.table.cellWidget(0,panel.COL_ECU).toolTip())
        panel.vehicle_selector.fn_set_vehicle('BENCH')
        self.assertEqual(panel.table.cellWidget(0,panel.COL_ECU).currentData().name,'TEST')
        panel.fn_set_vehicle(Vehicle('OTHER', ecus=[ECU('OTHER')]))
        self.assertEqual(panel.fn_current_sequence().steps[0].ecu,'TEST')
        self.assertIn('missing',panel.table.cellWidget(0,panel.COL_ECU).toolTip())

    def test_theme_refresh_keeps_runtime_and_definition_edit_invalidates_it(self):
        from gui.themes.theme_manager import ThemeManager
        from gui.themes.theme import ThemeType
        panel=self.make_panel()
        key=panel.step_ids[0]
        panel.set_step_result(key,'62 F1 90','Passed','Injected QA result, not transport execution')
        self.addCleanup(ThemeManager.fn_set_theme,ThemeManager.fn_theme())
        for theme in (ThemeType.DARK,ThemeType.LIGHT):
            ThemeManager.fn_set_theme(theme)
            panel.fn_refresh_theme()
            self.assertEqual(panel.table.item(0,panel.COL_RESULT).text(),'Passed')
            self.assertEqual(panel.table.item(0,panel.COL_RESULT).foreground().color().name(),ThemeManager.fn_colors().SUCCESS.lower())
            self.assertFalse(panel.fn_is_dirty())
        panel.table.item(0,panel.COL_COMMENT).setText('changed')
        self.assertEqual(panel.table.item(0,panel.COL_RESULT).text(),'—')

    def test_added_row_hidden_sequence_name_remains_native_saveable(self):
        import tempfile
        from pathlib import Path
        from repositories.diagnostic_sequence_repository import DiagnosticSequenceRepository
        panel=self.make_panel()
        panel.vehicle_selector.fn_set_vehicle('BENCH')
        panel.fn_add_step_after_selected()
        panel.table.item(1,panel.COL_REQUEST).setText('10 03')
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path=Path(directory)/'sequence.json'
            DiagnosticSequenceRepository(directory).fn_save_sequence(panel.fn_current_sequence(),path)
            self.assertEqual(DiagnosticSequenceRepository(directory).fn_load_sequence(path).steps[1].sequence_name,'TEST')
