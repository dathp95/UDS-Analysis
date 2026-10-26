import os
import unittest
from dataclasses import replace
from types import SimpleNamespace
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from core.diagnostic_sequence import DiagnosticStep,DiagnosticTestCase
from models.vehicle import Vehicle
from models.ecu import ECU
from gui.widgets.can_interface.diagnostic_table_panel import CanDiagnosticTablePanel


class StepRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        service=SimpleNamespace(list_vehicles=lambda:['BENCH','OTHER'],
            load_vehicle=lambda name:Vehicle(name,ecus=[ECU('BCM','681','601'),ECU('EPS','682','602')]))
        self.panel=CanDiagnosticTablePanel(vehicle_service=service)
        self.addCleanup(self.panel.deleteLater)
        self.case=DiagnosticTestCase(1,'VIN','',True,[DiagnosticStep(i,'VIN','BCM','22 F1 90',expected_response='62 F1 90') for i in range(1,6)])
        self.panel.fn_load_sequence(self.case)
        self.panel.vehicle_selector.fn_set_vehicle('BENCH')
        for i,key in enumerate(self.panel.step_ids): self.panel.set_step_result(key,f'62 F1 90 {i:02X}','Passed',f'RT {i}')
        self.original=dict(self.panel._runtime)
        self.ids=tuple(self.panel.step_ids)

    def test_steps_1_to_4_survive_step_5_bcm_to_eps_without_rebuilding(self):
        p=self.panel
        cells=[p.table.item(i,p.COL_RECEIVE) for i in range(4)]
        combo=p.table.cellWidget(4,p.COL_ECU)
        combo.setCurrentIndex(combo.findText('EPS'))
        self.assertEqual(tuple(p.step_ids),self.ids)
        for i,key in enumerate(self.ids[:4]):
            self.assertEqual(p._runtime[key],self.original[key])
            self.assertEqual(p.table.item(i,p.COL_RESULT).text(),'Passed')
            self.assertIs(p.table.item(i,p.COL_RECEIVE),cells[i])
        self.assertNotIn(self.ids[4],p._runtime)

    def test_comment_delay_repeat_keep_all_results(self):
        p=self.panel
        for column,value in ((p.COL_COMMENT,'note'),(p.COL_DELAY,'250'),(p.COL_REPEAT,'3')):
            p.table.item(0,column).setText(value)
            self.assertEqual(p._runtime,self.original)

    def test_payload_expected_and_match_invalidate_only_changed_step(self):
        p=self.panel
        for column,value in ((p.COL_REQUEST,'22 F1 91'),(p.COL_EXPECTED,'62 F1 91')):
            p.set_step_result(self.ids[0],'62 F1 90 00','Passed')
            p.table.item(0,column).setText(value)
            self.assertNotIn(self.ids[0],p._runtime)
            for key in self.ids[1:]: self.assertEqual(p._runtime[key],self.original[key])
        p.set_step_result(self.ids[0],'62 F1 91 00','Passed')
        steps=list(p.fn_current_sequence().steps);steps[0]=replace(steps[0],match='exact')
        p._replace_steps(steps);p._mark_dirty()
        self.assertNotIn(self.ids[0],p._runtime)
        self.assertEqual(tuple(p.step_ids),self.ids)

    def test_add_delete_preserve_surviving_results_and_sequence_load_resets(self):
        p=self.panel
        p.table.selectRow(2);p.fn_remove_selected_step()
        expected={key:value for key,value in self.original.items() if key!=self.ids[2]}
        self.assertEqual(p._runtime,expected)
        p.fn_add_step_after_selected()
        self.assertEqual(p._runtime,expected)
        p.fn_load_sequence(self.case)
        self.assertEqual(p._runtime,{})
        self.assertTrue(set(self.ids).isdisjoint(p.step_ids))

    def test_vehicle_switch_configuration_refresh_and_direct_set_clear_results(self):
        p=self.panel
        p.vehicle_selector.fn_set_vehicle('OTHER')
        self.assertEqual(p._runtime,{})
        p.set_step_result(self.ids[0],'62 F1 90','Passed')
        p.fn_refresh_vehicles()
        self.assertEqual(p._runtime,{})
        p.set_step_result(self.ids[0],'62 F1 90','Passed')
        p.fn_set_vehicle(Vehicle('NEW'))
        self.assertEqual(p._runtime,{})
