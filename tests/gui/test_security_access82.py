import tempfile
from pathlib import Path
from threading import get_ident
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox
from core.bench_authorization import BenchAuthorizationContext
from core.diagnostic_sequence import DiagnosticStep,DiagnosticTestCase
from gui.tabs.can_interface_tab import CANInterfaceTab
from gui.workers.can_connection_worker import CANConnectionOperation
from repositories.can_interface_ui_store import CanInterfaceUiStore
from repositories.can_sequence_repository import CanSequenceRepository
from models.ecu import ECU
from models.vehicle import Vehicle
from services.can import CANService,CANConfig
from services.can.simulated_backend import SimulatedCANBackend
from services.can.security_access_session import SecurityAccessState as State
from tests.gui import test_can_diagnostic_execution as fixtures


class SecurityAccess82GuiTests(unittest.TestCase):
    setUpClass=classmethod(fixtures.CanDiagnosticExecutionTests.setUpClass.__func__)
    wait=fixtures.CanDiagnosticExecutionTests.wait

    def setUp(self):
        directory=tempfile.TemporaryDirectory(dir=Path.cwd());self.addCleanup(directory.cleanup)
        root=Path(directory.name)
        self.backend=SimulatedCANBackend()
        self.service=CANService(self.backend)
        vehicle=Vehicle('BENCH',ecus=[ECU('BCM','681','601')])
        self.tab=CANInterfaceTab(self.service,vehicle_service=SimpleNamespace(list_vehicles=lambda:['BENCH'],load_vehicle=lambda _:vehicle),
            sequence_repository=CanSequenceRepository(root/'seq'),ui_store=CanInterfaceUiStore(root/'prefs'))
        self.addCleanup(self.tab.deleteLater);self.addCleanup(self.tab._connection_task.shutdown);self.addCleanup(self.tab.close)
        self.tab._on_sequence_selected(DiagnosticTestCase(1,'L1 simulator','',True,[
            DiagnosticStep(1,'Session','BCM','10 03',expected_response='50 03'),
            DiagnosticStep(2,'Seed','BCM','27 01',expected_response='67 01')]))
        self.panel=self.tab.sequence_table
        self.panel.vehicle_selector.fn_set_vehicle('BENCH')
        config=CANConfig('vector',0,500000,bench_context=BenchAuthorizationContext('simulator-bench',True))
        self.tab._connection_task.start(CANConnectionOperation.CONNECT,config)
        self.wait(lambda:not self.tab._connection_task.running)

    def outcome(self,row): return self.panel.table.item(row,self.panel.COL_RESULT).text()

    def seed(self):
        with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes):
            for row in (0,1):
                self.panel.table.selectRow(row)
                self.panel.table.cellWidget(row,self.panel.COL_SEND).click()
                self.wait(lambda:self.outcome(row)=='Passed')
        self.assertEqual(self.tab.diagnostic_controller.security_session.state,State.SEED_RECEIVED)

    def unlock(self,answer=QMessageBox.Yes):
        with patch.object(QMessageBox,'question',return_value=answer) as confirm:
            self.tab.session_panel.current_test_case.btn_unlock_l1.click()
            self.tab.session_panel.current_test_case.btn_unlock_l1.click()
            self.wait(lambda:not self.tab.diagnostic_controller._preparing)
            if answer==QMessageBox.Yes: self.wait(lambda:not self.tab._connection_task.diagnostic_busy)
        return confirm

    def test_complete_async_flow_same_owner_exact_unlock_and_theme(self):
        self.seed()
        self.assertTrue(self.tab.session_panel.current_test_case.btn_unlock_l1.isEnabled())
        self.assertNotIn('disabled', self.tab.session_panel.current_test_case.security_status.text())
        self.unlock().assert_called_once()
        self.assertEqual(self.tab.diagnostic_controller.security_session.state,State.UNLOCKED)
        self.assertEqual(self.outcome(1),'Passed')
        self.assertTrue(self.panel.table.item(1,self.panel.COL_RECEIVE).text().startswith('67 01 '))
        self.assertIn('67 02: Passed', self.tab.session_panel.current_test_case.key_result.text())
        self.assertIn('Simulator',self.tab.session_panel.current_test_case.security_status.text())
        self.assertEqual(sum(p[:2]==b'\x27\x02' for p in self.backend.requests),1)
        self.assertEqual(len(set(self.backend.threads)),1)
        self.assertNotEqual(self.backend.threads[0],get_ident())
        self.assertEqual(self.outcome(0),'Passed')
        self.assertEqual(self.panel.table.item(1,self.panel.COL_REQUEST).text(),'27 01')
        from gui.themes.theme_manager import ThemeManager
        from gui.themes.theme import ThemeType
        self.addCleanup(ThemeManager.fn_set_theme,ThemeManager.fn_theme())
        for theme in (ThemeType.DARK,ThemeType.LIGHT):
            ThemeManager.fn_set_theme(theme);self.tab.fn_refresh_theme()
            self.assertEqual(self.outcome(1),'Passed')

    def test_declined_key_confirmation_sends_no_key(self):
        self.seed();self.unlock(QMessageBox.No)
        self.assertEqual([p[:2] for p in self.backend.requests],[b'\x10\x03',b'\x27\x01'])
        self.assertEqual(self.tab.diagnostic_controller.security_session.state,State.CANCELLED)

    def test_invalid_key_nrc_never_unlocks_or_retries(self):
        self.backend.key_response=b'\x7f\x27\x35'
        self.seed();self.unlock()
        self.assertEqual(self.outcome(1),'Passed')  # The seed transaction stays successful.
        self.assertIn('Failed', self.tab.session_panel.current_test_case.key_result.text())
        self.assertEqual(self.tab.diagnostic_controller.security_session.state,State.FAILED)
        self.assertIn('NRC 0x35',self.panel.notice.text())
        self.assertEqual(sum(p[:2]==b'\x27\x02' for p in self.backend.requests),1)

    def test_calculation_off_gui_thread_edit_cancels_late_result(self):
        self.seed()
        provider=self.service.security_provider('BENCH','BCM');calculate=provider.calculate
        threads=[];ticks=[]
        timer=QTimer();timer.setInterval(5);timer.timeout.connect(lambda:ticks.append(1));timer.start()
        self.addCleanup(timer.stop)
        def slow(*args,**kwargs):
            import time
            threads.append(get_ident());time.sleep(.1)
            return calculate(*args,**kwargs)
        with patch.object(provider,'calculate',side_effect=slow):
            self.tab.session_panel.current_test_case.btn_unlock_l1.click()
            QTimer.singleShot(20,lambda:self.panel.table.item(1,self.panel.COL_COMMENT).setText('Edited'))
            self.wait(lambda:not self.tab.diagnostic_controller._preparing)
        self.assertNotEqual(threads,[get_ident()])
        self.assertGreater(len(ticks),2)
        self.assertFalse(any(p[:2]==b'\x27\x02' for p in self.backend.requests))

    def test_no_verified_provider_and_disconnect_keep_action_disabled(self):
        from services.can.hmac_sha1_provider import ProviderVerificationGate
        self.seed()
        self.service.security_gate=ProviderVerificationGate()
        self.tab.diagnostic_controller._refresh_security_status()
        self.assertFalse(self.tab.session_panel.current_test_case.btn_unlock_l1.isEnabled())
        self.tab.disconnect_can();self.wait(lambda:not self.tab._connection_task.running)
        self.assertFalse(self.tab.session_panel.current_test_case.btn_unlock_l1.isEnabled())

    def test_zero_seed_reports_already_unlocked_without_sending_key(self):
        self.backend.seed = bytes(16)
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes):
            for row in (0, 1):
                self.panel.table.selectRow(row)
                self.panel.table.cellWidget(row, self.panel.COL_SEND).click()
                self.wait(lambda: self.outcome(row) == 'Passed')
        self.assertEqual(self.tab.diagnostic_controller.security_session.state, State.UNLOCKED)
        self.assertIn('Simulator', self.tab.session_panel.current_test_case.security_status.text())
        self.assertFalse(self.tab.session_panel.current_test_case.btn_unlock_l1.isEnabled())
        self.assertFalse(any(p[:2] == b'\x27\x02' for p in self.backend.requests))

    def test_edit_during_confirmation_never_submits_calculated_key(self):
        self.seed()
        def edit_then_confirm(*_args):
            self.panel.table.item(1, self.panel.COL_COMMENT).setText('Changed during confirmation')
            return QMessageBox.Yes
        with patch.object(QMessageBox, 'question', side_effect=edit_then_confirm):
            self.tab.session_panel.current_test_case.btn_unlock_l1.click()
            self.wait(lambda: not self.tab.diagnostic_controller._preparing)
        self.assertFalse(any(p[:2] == b'\x27\x02' for p in self.backend.requests))

    def test_configured_can_ids_changed_inside_confirmation_never_send_key(self):
        self.seed()
        def change_ids_then_confirm(*_args):
            self.panel._vehicle_service.load_vehicle('BENCH').ecus[0].request_id = '682'
            return QMessageBox.Yes
        with patch.object(QMessageBox, 'question', side_effect=change_ids_then_confirm):
            self.tab.session_panel.current_test_case.btn_unlock_l1.click()
            self.wait(lambda: not self.tab.diagnostic_controller._preparing)
            self.wait(lambda: not self.tab._connection_task.diagnostic_busy)
        self.assertFalse(any(p[:2] == b'\x27\x02' for p in self.backend.requests))

    def test_backend_key_error_never_leaks_provider_exception_or_retries(self):
        self.seed()
        provider = self.service.security_provider('BENCH', 'BCM')
        with patch.object(provider, 'calculate', side_effect=RuntimeError('PRIVATE_PROVIDER_CONTENT')):
            self.tab.session_panel.current_test_case.btn_unlock_l1.click()
            self.wait(lambda: not self.tab.diagnostic_controller._preparing)
        self.assertNotIn('PRIVATE_PROVIDER_CONTENT', self.panel.notice.text())
        self.assertFalse(any(p[:2] == b'\x27\x02' for p in self.backend.requests))

    def test_key_response_pending_then_exact_final(self):
        self.seed()
        self.backend.pending_delay = .08
        self.unlock()
        self.wait(lambda: self.tab.diagnostic_controller.security_session.state == State.UNLOCKED)
        self.assertIn('NRC 0x78 count: 1', self.panel.notice.text())

    def test_expected_seed_mismatch_cannot_enable_unlock(self):
        self.panel.table.item(1, self.panel.COL_EXPECTED).setText('67 02')
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes):
            for row, outcome in ((0, 'Passed'), (1, 'Failed')):
                self.panel.table.selectRow(row)
                self.panel.table.cellWidget(row, self.panel.COL_SEND).click()
                self.wait(lambda: self.outcome(row) == outcome)
        self.assertFalse(self.tab.session_panel.current_test_case.btn_unlock_l1.isEnabled())
        self.assertFalse(self.tab.diagnostic_controller.security_session.has_seed)

    def test_key_exchange_preserves_the_seed_row_response(self):
        self.seed()
        received = self.panel.table.item(1, self.panel.COL_RECEIVE).text()
        self.unlock()
        self.assertEqual(self.panel.table.item(1, self.panel.COL_RECEIVE).text(), received)
        self.assertIn('67 02', self.tab.session_panel.current_test_case.key_result.text())

    def test_generated_key_frames_never_reach_monitor_or_recording_sink(self):
        captured = []
        session = self.tab._connection_task._worker.session
        session.capture_sink = captured.append
        self.seed(); self.unlock()
        self.wait(lambda: any(f.data[1:3] == b'\x67\x02' for f in self.tab.monitor_panel._buffer))
        for frames in (captured, self.tab.monitor_panel._buffer):
            self.assertFalse(any(f.direction == 'TX' and f.data[0] >> 4 in (1, 2) for f in frames))
        from dataclasses import replace
        private = next(f for f in self.backend.frames if f.direction == 'TX' and f.data[0] >> 4 == 1)
        count = len(captured)
        session._capture(replace(private, sequence=999, echo_of_sequence=private.sequence, tx_origin='echo'))
        self.assertEqual(len(captured), count)
        session._capture(replace(private, sequence=1000, echo_of_sequence=None, tx_origin='observed_echo'))
        self.assertEqual(len(captured), count)
