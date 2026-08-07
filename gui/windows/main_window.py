from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
)
from PySide6.QtGui import QKeySequence, QShortcut

from gui.tabs.log_analyzer_tab import LogAnalyzerTab
from gui.tabs.vehicle_manager_tab import VehicleManagerTab
from gui.themes.icon_manager import IconManager
from gui.themes.styles.containers.window_style import fn_window_style
from config.paths import SHORTCUTS_FILE
from shortcuts.shortcut_manager import load_shortcuts


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(" V-CODE v1.0.2 | AES EEIV by DAT TRAN")
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
            "toggle_theme": lambda: self.log_analyzer_tab.left_panel.theme_switch.switch_dark.click(),
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
        self.vehicle_manager_tab = VehicleManagerTab()

        self.tabs.addTab(
            self.log_analyzer_tab,
            "Log Analyzer",
        )
        self.tabs.addTab(
            self.vehicle_manager_tab,
            "Vehicle Manager",
        )

        self.vehicle_manager_tab.vehicle_data_changed.connect(
            lambda _vehicle_name: self.log_analyzer_tab.fn_refresh_vehicles()
        )

    def fn_refresh_theme(self):
        self.setStyleSheet(
            fn_window_style()
        )

        self.log_analyzer_tab.fn_refresh_theme()

        if hasattr(
            self.vehicle_manager_tab,
            "fn_refresh_theme",
        ):
            self.vehicle_manager_tab.fn_refresh_theme()

