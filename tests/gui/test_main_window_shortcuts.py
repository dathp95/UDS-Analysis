import os
import sys
import types
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication


class MainWindowShortcutTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_shortcuts_only_run_on_log_analyzer_tab(self):
        with patch.dict(
            sys.modules,
            {
                "can": types.SimpleNamespace(),
                "pandas": types.SimpleNamespace(),
            },
        ):
            from gui.windows.main_window import MainWindow

            with patch("gui.windows.main_window.load_shortcuts", return_value=[]):
                window = MainWindow()

        self.addCleanup(window.deleteLater)
        self.addCleanup(self._clear_imported_gui_modules)

        action = Mock()

        window.tabs.setCurrentWidget(window.vehicle_manager_tab)
        window._run_log_analyzer_shortcut(action)

        action.assert_not_called()

        window.tabs.setCurrentWidget(window.log_analyzer_tab)
        window._run_log_analyzer_shortcut(action)

        action.assert_called_once_with()

    def test_coding_value_tab_is_next_to_log_analyzer(self):
        with patch.dict(
            sys.modules,
            {
                "can": types.SimpleNamespace(),
                "pandas": types.SimpleNamespace(),
            },
        ):
            from gui.windows.main_window import MainWindow

            with patch("gui.windows.main_window.load_shortcuts", return_value=[]):
                window = MainWindow()

        self.addCleanup(window.deleteLater)
        self.addCleanup(self._clear_imported_gui_modules)

        self.assertIs(window.tabs.widget(0), window.log_analyzer_tab)
        self.assertIs(window.tabs.widget(1), window.coding_value_tab)
        self.assertEqual(window.tabs.tabText(1), "Coding value")
        self.assertIs(window.tabs.widget(2), window.crc_converter_tab)
        self.assertEqual(window.tabs.tabText(2), "CRC_Converter")
        self.assertIs(window.tabs.widget(3), window.vehicle_manager_tab)
        self.assertIs(window.tabs.widget(4), window.license_support_tab)
        self.assertEqual(window.tabs.tabText(4), "License & Support")

    def test_crc_converter_tab_is_available_with_crc_panel(self):
        with patch.dict(
            sys.modules,
            {
                "can": types.SimpleNamespace(),
                "pandas": types.SimpleNamespace(),
            },
        ):
            from gui.windows.main_window import MainWindow
            from gui.tabs.crc_converter_tab import CRCConverterTab

            with patch("gui.windows.main_window.load_shortcuts", return_value=[]):
                window = MainWindow()

        self.addCleanup(window.deleteLater)
        self.addCleanup(self._clear_imported_gui_modules)

        self.assertIsInstance(window.crc_converter_tab, CRCConverterTab)
        self.assertIsNotNone(window.crc_converter_tab.layout())
        self.assertGreater(window.crc_converter_tab.layout().count(), 0)
        self.assertEqual(
            window.crc_converter_tab.lbl_crc8_sae_j1850.text(),
            "CRC8_SAE_J1850",
        )

    def test_crc_transfer_signal_updates_coding_value_tab(self):
        with patch.dict(
            sys.modules,
            {
                "can": types.SimpleNamespace(),
                "pandas": types.SimpleNamespace(),
            },
        ):
            from core.coding_value import CodingValueRow
            from gui.windows.main_window import MainWindow

            with patch("gui.windows.main_window.load_shortcuts", return_value=[]):
                window = MainWindow()

        self.addCleanup(window.deleteLater)
        self.addCleanup(self._clear_imported_gui_modules)

        panel = window.coding_value_tab.coding_value_panel
        panel.table.set_rows([
            CodingValueRow(
                parameter="Payload CRC Byte",
                byte_pos="0",
                bit_pos="0",
                bit_length="8",
                raw_value="",
                decoded_value="",
                decoded_options=(),
            ),
        ])

        window.crc_converter_tab.crc_transfer_requested.emit("47")

        self.assertEqual(panel.table.item(0, 4).text(), "47")
    def test_license_support_tab_shows_support_and_contact_content(self):
        with patch.dict(
            sys.modules,
            {
                "can": types.SimpleNamespace(),
                "pandas": types.SimpleNamespace(),
            },
        ):
            from gui.windows.main_window import MainWindow
            from gui.tabs.license_support_tab import LicenseSupportTab

            with patch("gui.windows.main_window.load_shortcuts", return_value=[]):
                window = MainWindow()

        self.addCleanup(window.deleteLater)
        self.addCleanup(self._clear_imported_gui_modules)

        tab = window.license_support_tab
        self.assertIsInstance(tab, LicenseSupportTab)
        self.assertIn("Support the development", tab.title_label.text())
        self.assertIn("continued development", tab.description_label.text())
        self.assertFalse(tab.qr_label.pixmap().isNull())
        self.assertFalse(tab.qr_label.hasScaledContents())
        original_pixmap = tab.support_qr_pixmap
        displayed_pixmap = tab.qr_label.pixmap()
        self.assertAlmostEqual(
            original_pixmap.width() / original_pixmap.height(),
            displayed_pixmap.width() / displayed_pixmap.height(),
            places=2,
        )
        self.assertIn("tranducdat.eng@gmail.com", tab.email_label.text())
        self.assertIn("tranducdatks95@gmail.com", tab.email_label.text())
        self.assertEqual(tab.phone_label.text(), "Phone: 0329000529")

    @staticmethod
    def _clear_imported_gui_modules():
        modules_to_clear = {
            "core.convert_blf",
            "core.export_transactions",
            "core.pipeline",
            "core.report_export",
            "gui.controllers.analysis_controller",
            "gui.controllers.report_controller",
            "gui.tabs.coding_value_tab",
            "gui.tabs.crc_converter_tab",
            "gui.tabs.license_support_tab",
            "gui.tabs.log_analyzer_tab",
            "gui.windows.main_window",
        }
        for module_name in modules_to_clear:
            sys.modules.pop(module_name, None)
