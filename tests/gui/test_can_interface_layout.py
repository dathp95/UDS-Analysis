import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from gui.tabs.can_interface_tab import CANInterfaceTab
from tests.gui.test_can_interface_tab import FakeCANService


class CANInterfaceLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_three_splitters_and_single_service_owner(self):
        tab = CANInterfaceTab(FakeCANService())
        self.addCleanup(tab.deleteLater)
        self.addCleanup(tab.close)
        self.assertEqual(tab.main_splitter.orientation(), Qt.Horizontal)
        self.assertEqual(tab.right_splitter.orientation(), Qt.Vertical)
        self.assertEqual(tab.bottom_splitter.orientation(), Qt.Horizontal)
        self.assertIs(tab.main_splitter.widget(0), tab.sequence_list)
        self.assertIs(tab.right_splitter.widget(0), tab.sequence_table)
        self.assertIs(tab.bottom_splitter.widget(0), tab.session_panel)
        self.assertIs(tab.bottom_splitter.widget(1), tab.monitor_panel)
        self.assertIs(tab.connection_controller._service, tab._service)
        for width, height in ((1600, 900), (1366, 768)):
            tab.resize(width, height)
            tab.show()
            self.app.processEvents()
            self.assertGreater(tab.sequence_table.height(), height * .4)
            self.assertGreater(tab.session_panel.width(), 250)
            self.assertGreater(tab.monitor_panel.width(), 300)
