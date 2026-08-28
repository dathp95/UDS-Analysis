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
        self.assertIs(window.tabs.widget(3), window.can_interface_tab)
        self.assertEqual(window.tabs.tabText(3), "CAN Interface")
        self.assertIs(window.tabs.widget(4), window.vehicle_manager_tab)
        self.assertIs(window.tabs.widget(5), window.license_support_tab)
        self.assertEqual(window.tabs.tabText(5), "License & Support")



    def test_log_analyzer_prioritizes_result_table_width(self):
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

        content_layout = window.log_analyzer_tab.content_layout

        self.assertIs(content_layout.itemAt(0).widget(), window.log_analyzer_tab.left_panel)
        self.assertIs(content_layout.itemAt(1).widget(), window.log_analyzer_tab.tbl_result)
        self.assertIs(content_layout.itemAt(2).widget(), window.log_analyzer_tab.right_panel)
        self.assertEqual(content_layout.stretch(0), 2)
        self.assertEqual(content_layout.stretch(1), 9)
        self.assertEqual(content_layout.stretch(2), 2)

    def test_theme_switch_is_in_vehicle_manager_separate_bottom_layout(self):
        with patch.dict(
            sys.modules,
            {
                "can": types.SimpleNamespace(),
                "pandas": types.SimpleNamespace(),
            },
        ):
            from gui.windows.main_window import MainWindow
            from gui.widgets.controls.theme_switch import ThemeSwitch

            with patch("gui.windows.main_window.load_shortcuts", return_value=[]):
                window = MainWindow()

        self.addCleanup(window.deleteLater)
        self.addCleanup(self._clear_imported_gui_modules)

        self.assertFalse(hasattr(window.log_analyzer_tab.left_panel, "theme_switch"))
        self.assertIsInstance(window.vehicle_manager_tab.theme_switch, ThemeSwitch)

        detail_layout = window.vehicle_manager_tab.detail_scroll_area.widget().layout()
        action_layout = detail_layout.itemAt(1).layout()
        bottom_layout = detail_layout.itemAt(3).layout()

        self.assertIs(
            action_layout.itemAt(action_layout.count() - 1).widget(),
            window.vehicle_manager_tab.btn_save,
        )
        self.assertIsNone(
            action_layout.itemAt(action_layout.count() - 2).widget(),
        )
        self.assertIs(
            bottom_layout.itemAt(0).widget(),
            window.vehicle_manager_tab.theme_switch,
        )
        self.assertIsNone(
            bottom_layout.itemAt(bottom_layout.count() - 1).widget(),
        )

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

    def test_can_interface_tab_is_available_after_crc_converter(self):
        with patch.dict(
            sys.modules,
            {
                "can": types.SimpleNamespace(),
                "pandas": types.SimpleNamespace(),
            },
        ):
            from gui.windows.main_window import MainWindow
            from gui.tabs.can_interface_tab import CANInterfaceTab

            with patch("gui.windows.main_window.load_shortcuts", return_value=[]):
                window = MainWindow()

        self.addCleanup(window.deleteLater)
        self.addCleanup(self._clear_imported_gui_modules)

        self.assertIsInstance(window.can_interface_tab, CANInterfaceTab)
        self.assertIs(window.tabs.widget(3), window.can_interface_tab)
        self.assertEqual(window.can_interface_tab.cmb_vendor.currentText(), "Vector")
        self.assertEqual(window.can_interface_tab.cmb_channel.currentData(), 0)
        self.assertEqual(window.can_interface_tab.cmb_baudrate.currentData(), 500000)

    def test_release_config_disables_can_interface_tab(self):
        with patch.dict(
            sys.modules,
            {
                "can": types.SimpleNamespace(),
                "pandas": types.SimpleNamespace(),
            },
        ):
            from core.feature_access import Feature
            from gui.windows.main_window import MainWindow

            with patch("gui.windows.main_window.load_shortcuts", return_value=[]), patch(
                "gui.windows.main_window.load_deactivated_features",
                return_value={Feature.CAN_INTERFACE},
            ):
                window = MainWindow()

        self.addCleanup(window.deleteLater)
        self.addCleanup(self._clear_imported_gui_modules)

        self.assertEqual(window.tabs.tabText(3), "CAN Interface")
        self.assertFalse(window.tabs.isTabEnabled(3))

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

    def test_invalid_license_only_enables_free_tabs(self):
        with patch.dict(
            sys.modules,
            {
                "can": types.SimpleNamespace(),
                "pandas": types.SimpleNamespace(),
            },
        ):
            from gui.windows.main_window import MainWindow
            from license.manager import LicenseStatus

            with patch("gui.windows.main_window.load_shortcuts", return_value=[]):
                window = MainWindow(
                    license_status=LicenseStatus.invalid("test invalid")
                )

        self.addCleanup(window.deleteLater)
        self.addCleanup(self._clear_imported_gui_modules)

        self.assertFalse(window.tabs.isTabEnabled(0))
        self.assertFalse(window.tabs.isTabEnabled(1))
        self.assertTrue(window.tabs.isTabEnabled(2))
        self.assertFalse(window.tabs.isTabEnabled(3))
        self.assertFalse(window.tabs.isTabEnabled(4))
        self.assertTrue(window.tabs.isTabEnabled(5))
        self.assertIs(window.tabs.currentWidget(), window.crc_converter_tab)

    def test_valid_license_enables_all_tabs(self):
        with patch.dict(
            sys.modules,
            {
                "can": types.SimpleNamespace(),
                "pandas": types.SimpleNamespace(),
            },
        ):
            from gui.windows.main_window import MainWindow
            from license.manager import LicenseStatus

            with patch("gui.windows.main_window.load_shortcuts", return_value=[]):
                window = MainWindow(
                    license_status=LicenseStatus.valid()
                )

        self.addCleanup(window.deleteLater)
        self.addCleanup(self._clear_imported_gui_modules)

        for index in range(window.tabs.count()):
            self.assertTrue(window.tabs.isTabEnabled(index))

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
            "gui.tabs.can_interface_tab",
            "gui.tabs.crc_converter_tab",
            "gui.tabs.license_support_tab",
            "gui.tabs.log_analyzer_tab",
            "gui.windows.main_window",
        }
        for module_name in modules_to_clear:
            sys.modules.pop(module_name, None)

