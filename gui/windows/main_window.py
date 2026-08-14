from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
)
from PySide6.QtGui import QKeySequence, QShortcut

from core.feature_access import Feature, is_feature_enabled
from gui.tabs.coding_value_tab import CodingValueTab
from gui.tabs.crc_converter_tab import CRCConverterTab
from gui.tabs.license_support_tab import LicenseSupportTab
from gui.tabs.log_analyzer_tab import LogAnalyzerTab
from gui.tabs.vehicle_manager_tab import VehicleManagerTab
from gui.themes.icon_manager import IconManager
from gui.themes.styles.containers.window_style import fn_window_style
from config.paths import SHORTCUTS_FILE
from shortcuts.shortcut_manager import load_shortcuts


class MainWindow(QMainWindow):

    def __init__(self, license_status=None):
        super().__init__()

        self.license_status = license_status

        self.setWindowTitle("V-CODE v2.0.1 | AES EEIV by DAT TRAN")
        self.setWindowIcon(
            IconManager.app()
        )
        self.resize(1200, 800)

        self.setup_ui()
        self._setup_shortcuts()
        self.fn_refresh_theme()

    def _setup_shortcuts(self):
        actions = {
            "open_log": lambda: self.log_analyzer_tab.log_selector.browse_file(),
            "export_report": lambda: self.log_analyzer_tab.fn_export_clicked(),
            "search": lambda: self.log_analyzer_tab.filter_box.set_focus(),
            "clear": lambda: self.log_analyzer_tab.fn_clear_clicked(),
            "analyze": lambda: self.log_analyzer_tab.fn_run_clicked(),
            "add_quick_access": lambda: self.log_analyzer_tab.left_panel.quick_access.fn_add_filter(),
            "vehicle_selector": lambda: self.log_analyzer_tab.vehicle_selector.cmb_vehicle.setFocus(),
            "toggle_theme": lambda: self.vehicle_manager_tab.theme_switch.switch_dark.click(),
            "copy_asc": lambda: self.log_analyzer_tab.fn_copy_clicked(),
            "clone_quick_access": lambda: self.log_analyzer_tab.left_panel.quick_access.fn_clone_selected(),
        }
        self._shortcuts = []
        for item in load_shortcuts(SHORTCUTS_FILE):
            sequence = item.get("key")
            action = actions.get(item.get("action"))
            if not sequence or action is None:
                continue
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(
                lambda action=action: self._run_log_analyzer_shortcut(action)
            )
            self._shortcuts.append(shortcut)

    def _run_log_analyzer_shortcut(self, action):
        if self.tabs.currentWidget() != self.log_analyzer_tab:
            return

        action()

    def setup_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.log_analyzer_tab = LogAnalyzerTab()
        self.coding_value_tab = CodingValueTab()
        self.crc_converter_tab = CRCConverterTab()
        self.vehicle_manager_tab = VehicleManagerTab()
        self.license_support_tab = LicenseSupportTab()

        self._feature_tabs = (
            (
                self.log_analyzer_tab,
                "Log Analyzer",
                Feature.LOG_ANALYZER,
            ),
            (
                self.coding_value_tab,
                "Coding value",
                Feature.CODING_VALUE,
            ),
            (
                self.crc_converter_tab,
                "CRC_Converter",
                Feature.CRC_CONVERTER,
            ),
            (
                self.vehicle_manager_tab,
                "Vehicle Manager",
                Feature.VEHICLE_MANAGER,
            ),
            (
                self.license_support_tab,
                "License & Support",
                Feature.LICENSE_SUPPORT,
            ),
        )

        for tab, label, _feature in self._feature_tabs:
            self.tabs.addTab(
                tab,
                label,
            )

        self._apply_feature_access()

        self.vehicle_manager_tab.vehicle_data_changed.connect(
            lambda _vehicle_name: self.log_analyzer_tab.fn_refresh_vehicles()
        )

        self.crc_converter_tab.crc_transfer_requested.connect(
            self.coding_value_tab.fn_set_crc_value
        )

    def _apply_feature_access(self):
        license_is_valid = self._license_is_valid()

        for tab, _label, feature in self._feature_tabs:
            tab_index = self.tabs.indexOf(tab)
            if tab_index < 0:
                continue

            self.tabs.setTabEnabled(
                tab_index,
                is_feature_enabled(
                    feature,
                    license_is_valid=license_is_valid,
                ),
            )

        self._select_first_enabled_tab()

    def _select_first_enabled_tab(self):
        for index in range(self.tabs.count()):
            if self.tabs.isTabEnabled(index):
                self.tabs.setCurrentIndex(index)
                return

    def _license_is_valid(self):
        if self.license_status is None:
            return True

        return bool(self.license_status.is_valid)

    def fn_refresh_theme(self):
        self.setStyleSheet(
            fn_window_style()
        )

        self.log_analyzer_tab.fn_refresh_theme()

        self.coding_value_tab.fn_refresh_theme()

        if hasattr(
            self.crc_converter_tab,
            "fn_refresh_theme",
        ):
            self.crc_converter_tab.fn_refresh_theme()

        if hasattr(
            self.vehicle_manager_tab,
            "fn_refresh_theme",
        ):
            self.vehicle_manager_tab.fn_refresh_theme()

        if hasattr(
            self.license_support_tab,
            "fn_refresh_theme",
        ):
            self.license_support_tab.fn_refresh_theme()
