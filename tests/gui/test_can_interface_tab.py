import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from core.diagnostic_sequence import DiagnosticStep, DiagnosticTestCase

from gui.tabs.can_interface_tab import CANInterfaceTab
from gui.widgets.diagnostic import (
    DiagnosticSequenceList,
    DiagnosticSequenceTable,
)


class FakeCANService:

    def __init__(self):
        self.config = None
        self.connected = False
        self.refresh_count = 0
        self.connect_error = None

    def fn_connect(self, config):
        if self.connect_error is not None:
            raise self.connect_error
        self.config = config
        self.connected = True

    def fn_disconnect(self):
        self.connected = False

    def fn_is_connected(self):
        return self.connected

    def fn_refresh(self):
        self.refresh_count += 1
        return None


class CANInterfaceTabTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_initial_values_and_button_states(self):
        tab = CANInterfaceTab(service=FakeCANService())
        self.addCleanup(tab.deleteLater)

        self.assertEqual(tab.cmb_vendor.currentText(), "Vector")
        self.assertEqual(tab.cmb_device.currentText(), "VN1630A")
        self.assertEqual(tab.cmb_channel.currentText(), "CAN 1")
        self.assertEqual(tab.cmb_baudrate.currentData(), 500000)
        self.assertEqual(tab.lbl_status.text(), "â— Disconnected")
        self.assertTrue(tab.btn_connect.isEnabled())
        self.assertFalse(tab.btn_disconnect.isEnabled())

    def test_action_buttons_and_status_are_in_the_same_row(self):
        tab = CANInterfaceTab(service=FakeCANService())
        self.addCleanup(tab.deleteLater)

        self.assertIs(tab.action_layout.itemAt(0).widget(), tab.btn_refresh)
        self.assertIs(tab.action_layout.itemAt(1).widget(), tab.btn_connect)
        self.assertIs(tab.action_layout.itemAt(2).widget(), tab.btn_disconnect)
        self.assertIs(tab.action_layout.itemAt(3).widget(), tab.lbl_status)
        self.assertGreaterEqual(
            tab.lbl_status.minimumHeight(),
            tab.btn_connect.minimumHeight(),
        )

    def test_diagnostic_sequence_list_and_table_editor_are_available(self):
        tab = CANInterfaceTab(service=FakeCANService())
        self.addCleanup(tab.deleteLater)

        self.assertIsInstance(tab.sequence_list, DiagnosticSequenceList)
        self.assertIsInstance(tab.sequence_table, DiagnosticSequenceTable)

    def test_sequence_selected_loads_center_table(self):
        tab = CANInterfaceTab(service=FakeCANService())
        self.addCleanup(tab.deleteLater)
        test_case = DiagnosticTestCase(
            schema_version=1,
            name="READ VIN",
            description="",
            enabled=True,
            steps=[
                DiagnosticStep(
                    step=1,
                    sequence_name="Read VIN",
                    ecu="ACU",
                    request="22 F1 90",
                )
            ],
        )

        tab._on_sequence_selected(test_case)

        self.assertEqual(tab.sequence_table.table.rowCount(), 1)
        self.assertEqual(
            tab.sequence_table.table.item(
                0,
                tab.sequence_table.COL_REQUEST,
            ).text(),
            "22 F1 90",
        )

    def test_connect_uses_selected_channel_and_bitrate(self):
        service = FakeCANService()
        tab = CANInterfaceTab(service=service)
        self.addCleanup(tab.deleteLater)

        tab.cmb_channel.setCurrentIndex(1)
        tab.cmb_baudrate.setCurrentIndex(3)
        tab.connect_can()

        self.assertEqual(service.config.interface, "vector")
        self.assertEqual(service.config.channel, 1)
        self.assertEqual(service.config.bitrate, 1000000)
        self.assertEqual(tab.lbl_status.text(), "â— Connected")
        self.assertFalse(tab.btn_connect.isEnabled())
        self.assertTrue(tab.btn_disconnect.isEnabled())

    def test_connect_error_updates_status_without_crash(self):
        service = FakeCANService()
        service.connect_error = RuntimeError("Invalid Vector CAN channel.")
        tab = CANInterfaceTab(service=service)
        self.addCleanup(tab.deleteLater)

        with patch("gui.tabs.can_interface_tab.QMessageBox.warning"):
            tab.connect_can()

        self.assertEqual(tab.lbl_status.text(), "â— Error")
        self.assertIn("Invalid Vector CAN channel", tab.lbl_status.toolTip())
        self.assertTrue(tab.btn_connect.isEnabled())
        self.assertFalse(tab.btn_disconnect.isEnabled())

    def test_disconnect_returns_to_disconnected_state(self):
        service = FakeCANService()
        tab = CANInterfaceTab(service=service)
        self.addCleanup(tab.deleteLater)

        tab.connect_can()
        tab.disconnect_can()

        self.assertFalse(service.connected)
        self.assertEqual(tab.lbl_status.text(), "â— Disconnected")
        self.assertTrue(tab.btn_connect.isEnabled())
        self.assertFalse(tab.btn_disconnect.isEnabled())

    def test_refresh_does_not_fake_hardware_enumeration(self):
        service = FakeCANService()
        tab = CANInterfaceTab(service=service)
        self.addCleanup(tab.deleteLater)

        tab.refresh_can_setup()

        self.assertEqual(service.refresh_count, 1)
        self.assertEqual(tab.cmb_channel.count(), 4)
        self.assertEqual(tab.lbl_status.text(), "â— Disconnected")


if __name__ == "__main__":
    unittest.main()
