from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
)

from gui.tabs.log_analyzer_tab import LogAnalyzerTab
from gui.tabs.vehicle_manager_tab import VehicleManagerTab
from gui.themes.icon_manager import IconManager
from gui.themes.styles.containers.window_style import fn_window_style


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(" V-CODE v1.0.1 | AES EEIV by DAT TRAN")
        self.setWindowIcon(
            IconManager.app()
        )
        self.resize(1200, 800)

        self.setup_ui()
        self.fn_refresh_theme()

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
