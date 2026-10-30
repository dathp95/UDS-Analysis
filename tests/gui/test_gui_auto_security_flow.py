import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QMessageBox
from core.bench_authorization import BenchAuthorizationContext
from core.diagnostic_sequence import DiagnosticStep, DiagnosticTestCase
from gui.tabs.can_interface_tab import CANInterfaceTab
from gui.workers.can_connection_worker import CANConnectionOperation
from repositories.can_interface_ui_store import CanInterfaceUiStore
from repositories.can_sequence_repository import CanSequenceRepository
from services.can import CANService, CANConfig
from services.can.simulated_backend import SimulatedCANBackend
from services.can.security_access_session import SecurityAccessState as State
from services.vehicle_service import VehicleService
from tests.gui import test_can_diagnostic_execution as fixtures


class GuiAutoSecurityFlowTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.CanDiagnosticExecutionTests.setUpClass.__func__)
    wait = fixtures.CanDiagnosticExecutionTests.wait

    def setUp(self):
        directory = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.backend = SimulatedCANBackend()
        self.service = CANService(self.backend)
        self.vehicle_service = VehicleService()
        self.tab = CANInterfaceTab(
            self.service,
            vehicle_service=self.vehicle_service,
            sequence_repository=CanSequenceRepository(root / 'seq'),
            ui_store=CanInterfaceUiStore(root / 'prefs'),
        )
        self.addCleanup(self.tab.deleteLater)
        self.addCleanup(self.tab._connection_task.shutdown)
        self.addCleanup(self.tab.close)

        # 3 steps: Extended Session, 27 01 (L1), 27 03 (L2)
        test_case = DiagnosticTestCase(
            1, 'Full Auto Security Flow', '', True, [
                DiagnosticStep(1, 'Extended Session', 'BCM', '10 03', expected_response='50 03'),
                DiagnosticStep(2, 'Auto Unlock L1', 'BCM', '27 01', expected_response='67 02'),
                DiagnosticStep(3, 'Auto Unlock L2', 'BCM', '27 03', expected_response='67 04'),
            ]
        )
        self.tab._on_sequence_selected(test_case)
        self.panel = self.tab.sequence_table
        self.panel.vehicle_selector.fn_set_vehicle('VF5NP')

        config = CANConfig('vector', 0, 500000, bench_context=BenchAuthorizationContext('sim-bench', True))
        self.tab._connection_task.start(CANConnectionOperation.CONNECT, config)
        self.wait(lambda: not self.tab._connection_task.running)

    def outcome(self, row):
        item = self.panel.table.item(row, self.panel.COL_RESULT)
        return item.text() if item else ''

    def receive(self, row):
        item = self.panel.table.item(row, self.panel.COL_RECEIVE)
        return item.text() if item else ''

    def test_unlock_button_is_hidden(self):
        # Verification of user requirement: remove/hide Unlock L1 button from session panel
        self.assertFalse(self.tab.session_panel.current_test_case.btn_unlock_l1.isVisible())
        self.assertFalse(self.tab.session_panel.current_test_case.key_result.isVisible())

    def test_full_auto_flow_l1_and_l2(self):
        # Step 1: Run 10 03
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes):
            self.panel.table.selectRow(0)
            self.panel.table.cellWidget(0, self.panel.COL_SEND).click()
            self.wait(lambda: self.outcome(0) == 'Passed')
        self.assertEqual(self.receive(0), '50 03')

        # Step 2: Run 27 01 with single click -> should automatically calculate with BCM.dll and receive 67 02!
        seed_l1 = bytes.fromhex('adbeb3dd50ef2e87052cdce050f651b2')
        expected_key_l1 = bytes.fromhex('c141495385515aa08a006885b67815ac')
        self.backend.seed = seed_l1
        self.backend.expected_key = expected_key_l1

        self.panel.table.selectRow(1)
        self.panel.table.cellWidget(1, self.panel.COL_SEND).click()
        self.wait(lambda: self.outcome(1) == 'Passed')

        self.assertEqual(self.receive(1), '67 02')
        self.assertEqual(self.outcome(1), 'Passed')
        self.assertEqual(self.tab.diagnostic_controller.security_session.state, State.UNLOCKED)

        # Step 3: Run 27 03 with single click -> should automatically calculate L2 key with BCM.dll and receive 67 04!
        seed_l2 = bytes.fromhex('0d84466fdfd1a53c4c3f6f606661c113')
        expected_key_l2 = bytes.fromhex('4a04f887df23553b9e2a53a6d74e43a5')
        self.backend.seed = seed_l2
        self.backend.expected_key = expected_key_l2

        self.panel.table.selectRow(2)
        self.panel.table.cellWidget(2, self.panel.COL_SEND).click()
        self.wait(lambda: self.outcome(2) == 'Passed')

        self.assertEqual(self.receive(2), '67 04')
        self.assertEqual(self.outcome(2), 'Passed')
        self.assertEqual(self.tab.diagnostic_controller.security_session.state, State.UNLOCKED)
