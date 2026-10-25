import os
import tempfile
import unittest
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import QObject, Signal
from types import SimpleNamespace
from gui.tabs.can_interface_tab import CANInterfaceTab
from core.diagnostic_sequence import DiagnosticStep, DiagnosticTestCase
from repositories.can_interface_ui_store import CanInterfaceUiStore
from tests.gui.test_can_interface_tab import FakeCANService


class CanSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])

    def test_selected_row_details_are_read_only_and_update_after_edit(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            tab=CANInterfaceTab(FakeCANService(),ui_store=CanInterfaceUiStore(Path(directory)/'ui'))
            self.addCleanup(tab.deleteLater)
            self.addCleanup(tab.close)
            tab._on_sequence_selected(DiagnosticTestCase(1,'Bench','',True,[DiagnosticStep(1,'Bench','TEST','22 F1 90',100,2,'62 F1 90')]))
            tab.sequence_table.table.setCurrentCell(0,tab.sequence_table.COL_REQUEST)
            panel=tab.session_panel.current_test_case
            self.assertEqual(panel.values['Step'].text(),'1 / 1')
            self.assertEqual(panel.values['ECU'].text(),'TEST')
            self.assertEqual(panel.values['Payload'].text(),'22 F1 90')
            tab.sequence_table.table.item(0,tab.sequence_table.COL_REQUEST).setText('10 03')
            self.assertEqual(panel.values['Payload'].text(),'10 03')
            self.assertFalse(hasattr(panel,'btn_send'))

    def test_host_vehicle_manager_event_rebinds_canonical_ecus(self):
        from models.vehicle import Vehicle
        from models.ecu import ECU
        class Manager(QObject):
            vehicle_data_changed=Signal(str)
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            vehicle=[Vehicle('BENCH',ecus=[ECU('TEST')])]
            service=SimpleNamespace(list_vehicles=lambda:['BENCH'],load_vehicle=lambda _:vehicle[0])
            host=QWidget()
            host.vehicle_manager_tab=Manager(host)
            tab=CANInterfaceTab(FakeCANService(),vehicle_service=service,ui_store=CanInterfaceUiStore(Path(directory)/'ui'))
            QVBoxLayout(host).addWidget(tab)
            self.addCleanup(host.deleteLater)
            self.addCleanup(host.close)
            self.addCleanup(tab.close)
            host.show()
            self.app.processEvents()
            tab._on_sequence_selected(DiagnosticTestCase(1,'Bench','',True,[DiagnosticStep(1,'Bench','TEST','22 F1 90')]))
            tab.sequence_table.vehicle_selector.fn_set_vehicle('BENCH')
            self.assertEqual(tab.sequence_table.table.cellWidget(0,tab.sequence_table.COL_ECU).currentData().name,'TEST')
            vehicle[0]=Vehicle('BENCH',ecus=[ECU('NEW')])
            host.vehicle_manager_tab.vehicle_data_changed.emit('BENCH')
            self.assertEqual(tab.sequence_table.fn_current_sequence().steps[0].ecu,'TEST')
            self.assertIn('missing',tab.sequence_table.table.cellWidget(0,tab.sequence_table.COL_ECU).toolTip())
