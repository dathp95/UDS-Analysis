import unittest
from dataclasses import replace
from unittest.mock import patch

from PySide6.QtWidgets import QMessageBox
from core.diagnostic_request import DiagnosticSettings
from core.diagnostic_sequence import DiagnosticStep, DiagnosticTestCase
from tests.gui import test_can_diagnostic_execution as fixtures


class SecuritySeedGuiTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.CanDiagnosticExecutionTests.setUpClass.__func__)
    setUp = fixtures.CanDiagnosticExecutionTests.setUp
    wait = fixtures.CanDiagnosticExecutionTests.wait
    click = fixtures.CanDiagnosticExecutionTests.click
    outcome = fixtures.CanDiagnosticExecutionTests.outcome

    def configure(self, text='27 01'):
        panel = self.tab.sequence_table
        panel.table.item(0,panel.COL_REQUEST).setText(text)
        panel.table.item(0,panel.COL_EXPECTED).setText('67 01')
        return panel

    def test_exact_seed_ui_guard_whitespace_invalid_hex_unresolved_and_disconnected(self):
        panel = self.configure(' \t27\u00a001\n')
        button = panel.table.cellWidget(0,panel.COL_SEND)
        self.assertTrue(button.isEnabled())
        sent = []
        panel.row_send_requested.connect(sent.append)
        for text in ('27 02','27 03','27 01 00','27 0a','27 81','27','2701','27 0G','0x27 01',''):
            panel.table.item(0,panel.COL_REQUEST).setText(text)
            self.assertFalse(panel.table.cellWidget(0,panel.COL_SEND).isEnabled(),text)
            panel._request_step(panel.step_ids[0])
        self.assertEqual(sent,[])
        panel.fn_load_sequence(DiagnosticTestCase(1,'Seed','',True,[DiagnosticStep(1,'Seed','MISSING','27 01')]))
        self.assertFalse(panel.table.cellWidget(0,panel.COL_SEND).isEnabled())
        panel._request_step(panel.step_ids[0]);self.assertEqual(sent,[])
        panel.fn_load_sequence(DiagnosticTestCase(1,'Seed','',True,[DiagnosticStep(1,'Seed','BCM','27 01')]))
        self.assertTrue(panel.table.cellWidget(0,panel.COL_SEND).isEnabled())
        self.tab.disconnect_can();self.wait(lambda:not self.tab._connection_task.running)
        self.assertFalse(panel.table.cellWidget(0,panel.COL_SEND).isEnabled())
        self.assertEqual(self.bus.sent,[])

    def test_manual_single_frame_seed_shown_full_no_auto_session_key_or_dll(self):
        panel = self.configure(' \t27 01\n')
        self.bus.mode = 'seed'
        original = self.bus.send
        def seed_send(message, timeout):
            original(message, timeout)
            if bytes(message.data[:3]) == b'\x02\x27\x01':
                self.bus.rx('01 AA 00 00 00 00 00 00',0x123)
                self.bus.rx('04 67 01 AB CD 00 00 00')
        self.bus.send = seed_send
        with patch('ctypes.CDLL',side_effect=AssertionError('No DLL')), \
             patch('ctypes.WinDLL',side_effect=AssertionError('No DLL')), \
             patch.object(QMessageBox,'question',return_value=QMessageBox.Yes) as confirm:
            self.click()
            self.wait(lambda:self.outcome()=='Passed')
        confirm.assert_called_once()
        self.assertEqual(panel.table.item(0,panel.COL_RECEIVE).text(),'67 01 AB CD')
        self.assertEqual([bytes(message.data) for message in self.bus.sent],
                         [bytes.fromhex('02 27 01 00 00 00 00 00')])
        self.assertNotIn('AB CD',panel.notice.text())
        self.wait(lambda:self.tab.monitor_panel.frames>=3)
        self.assertTrue(any(item.can_id==0x123 for item in self.tab.monitor_panel._buffer))
        self.assertEqual(len(set(self.bus.threads)),1)
        from gui.themes.theme_manager import ThemeManager
        from gui.themes.theme import ThemeType
        self.addCleanup(ThemeManager.fn_set_theme,ThemeManager.fn_theme())
        for theme in (ThemeType.DARK,ThemeType.LIGHT):
            ThemeManager.fn_set_theme(theme);self.tab.fn_refresh_theme()
            self.assertEqual(panel.table.item(0,panel.COL_RECEIVE).text(),'67 01 AB CD')

    def test_multiframe_seed_flow_control_and_complete_receive_message(self):
        panel = self.configure()
        self.bus.mode = 'seed'
        original = self.bus.send
        def seed_send(message, timeout):
            original(message, timeout)
            if bytes(message.data[:3]) == b'\x02\x27\x01':
                self.bus.rx('10 12 67 01 00 01 02 03')
            elif message.data[0] == 0x30:
                self.bus.rx('21 04 05 06 07 08 09 0A')
                self.bus.rx('22 0B 0C 0D 0E 0F 00 00')
        self.bus.send = seed_send
        with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes):
            self.click();self.wait(lambda:self.outcome()=='Passed')
        self.assertEqual(panel.table.item(0,panel.COL_RECEIVE).text(),(b'\x67\x01'+bytes(range(16))).hex(' ').upper())
        self.assertEqual([bytes(message.data)[0] for message in self.bus.sent],[0x02,0x30])
        self.wait(lambda:self.tab.monitor_panel.frames>=5)

    def test_declined_confirmation_and_edit_cancellation_ignore_late_seed(self):
        panel = self.configure()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.No): self.click()
        self.assertEqual(self.bus.sent,[])
        self.bus.mode = 'silent'
        self.tab.diagnostic_controller.settings = DiagnosticSettings(p2_s=.3,p2_star_s=.5,total_s=2)
        with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes): self.click()
        self.wait(lambda:len(self.bus.sent)==1)
        panel.table.item(0,panel.COL_REQUEST).setText('22 F1 91')
        self.wait(lambda:not self.tab._connection_task.diagnostic_busy)
        self.bus.rx('04 67 01 AB CD 00 00 00')
        self.wait(lambda:len(self.bus.queue)==0)
        self.assertNotEqual(self.outcome(),'Passed')
        self.assertEqual(panel._runtime,{})
