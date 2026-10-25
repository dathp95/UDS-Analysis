import os
import unittest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from gui.widgets.can_interface.can_monitor_panel import CanMonitorPanel


class CanMonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])

    def test_empty_honest_shell_and_bounded_filtered_display(self):
        from core.can_interface_view import CanFrameView
        monitor=CanMonitorPanel(capacity=2)
        self.addCleanup(monitor.deleteLater)
        self.assertEqual(monitor.table.rowCount(),0)
        self.assertFalse(monitor.btn_export.isEnabled())
        self.assertFalse(monitor.btn_blf.isEnabled())
        self.assertIn('Not monitoring',monitor.status.text())
        monitor.append_frame_batch([CanFrameView(1.0,'TX',0x123,1,b'\x01'), CanFrameView(2.0,'RX',0x456,1,b'\x02'),CanFrameView(3.0,'RX',0x123,1,b'\x03')])
        self.assertEqual((monitor.frames,monitor.displayed,monitor.dropped),(3,2,1))
        monitor.edit_can_id.setText('123')
        self.assertEqual(monitor.table.rowCount(),1)
        self.assertEqual(monitor.table.item(0,4).text(),'03')
        monitor.cmb_direction.setCurrentText('TX')
        self.assertEqual(monitor.displayed,0)
        monitor.edit_can_id.setText('invalid')
        self.assertIn('Invalid',monitor.feedback.text())
        monitor.clear_display()
        self.assertEqual((monitor.frames,monitor.displayed,monitor.dropped),(0,0,0))

