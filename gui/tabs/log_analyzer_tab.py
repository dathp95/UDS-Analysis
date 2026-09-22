from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
)

from gui.controllers.analysis_controller import AnalysisController
from gui.controllers.clipboard_controller import ClipboardController
from gui.controllers.report_controller import ReportController
from gui.presenters.transaction_presenter import fn_build_table_rows
from gui.widgets.log_analyzer.filter_box import FilterBox
from gui.widgets.log_analyzer.left_panel import LeftPanel
from gui.widgets.log_analyzer.path_selector import PathSelectorWidget
from gui.widgets.log_analyzer.result_table import ResultTable
from gui.widgets.log_analyzer.right_panel import RightPanel
from gui.widgets.vehicle_manager.vehicle_selector import VehicleSelectorWidget
from services.vehicle_service import VehicleService
from core.log_validation import has_multiple_pt_bo_info_markers


class LogAnalyzerTab(QWidget):

    def __init__(self):
        super().__init__()

        # Runtime data
        self.pipeline_result = None
        self._current_vehicle = None

        # Controllers
        self._create_controllers()

        # Build UI
        self.setup_ui()

        # Connect signals
        self._connect_signals()

        # Initial UI state
        self.right_panel.action_panel.fn_set_startup_state()
        self.left_panel.fn_disable_quick_access()
        self._load_vehicles()

        self.fn_refresh_theme()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        input_layout = QHBoxLayout()
        self.content_layout = QHBoxLayout()

        main_layout.setSpacing(8)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)

        self.vehicle_selector = VehicleSelectorWidget()

        self.log_selector = PathSelectorWidget(
            "Log File: Supported logs Diagnostic only - NO: PT, CH, BO, IF...",
            "Log Files (*.blf *.asc)",
        )

        input_label_height = max(
            self.vehicle_selector.lbl_vehicle.sizeHint().height(),
            self.log_selector.label.sizeHint().height(),
        )

        self.vehicle_selector.lbl_vehicle.setFixedHeight(
            input_label_height
        )

        self.log_selector.label.setFixedHeight(
            input_label_height
        )

        self.filter_box = FilterBox()

        self.left_panel = LeftPanel()
        self.tbl_result = ResultTable()
        self.right_panel = RightPanel()

        self.content_layout.addWidget(self.left_panel, 2)
        self.content_layout.addWidget(self.tbl_result, 9)
        self.content_layout.addWidget(self.right_panel, 2)

        input_layout.addWidget(
            self.vehicle_selector,
            2,
            Qt.AlignTop,
        )

        input_layout.addWidget(
            self.log_selector,
            9,
            Qt.AlignTop,
        )

        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.filter_box)
        main_layout.addLayout(self.content_layout)

    def _create_controllers(self):
        self.analysis_controller = AnalysisController()
        self.export_controller = ReportController()
        self.clipboard_controller = ClipboardController()
        self.vehicle_service = VehicleService()

    def _connect_signals(self):
        self.vehicle_selector.vehicle_changed.connect(
            self.fn_vehicle_changed
        )

        self.log_selector.path_changed.connect(
            self.fn_log_file_changed
        )

        self.filter_box.filter_changed.connect(
            self.fn_filter_transactions
        )

        self.right_panel.action_panel.analyze_clicked.connect(
            self.fn_run_clicked
        )

        self.right_panel.action_panel.export_clicked.connect(
            self.fn_export_clicked
        )

        self.right_panel.action_panel.copy_clicked.connect(
            self.fn_copy_clicked
        )

        self.right_panel.action_panel.clear_clicked.connect(
            self.fn_clear_clicked
        )

        self.left_panel.quick_filter_selected.connect(
            self.fn_quick_filter
        )

    def _load_vehicles(self):
        self.fn_refresh_vehicles()

    def fn_refresh_vehicles(
        self,
        selected_vehicle_name: str = "",
    ) -> None:

        vehicles = self.vehicle_service.list_vehicles()

        if not selected_vehicle_name and self._current_vehicle is not None:

            selected_vehicle_name = self._current_vehicle.name

        if (
            selected_vehicle_name
            and selected_vehicle_name not in vehicles
        ):

            selected_vehicle_name = ""

        self.vehicle_selector.fn_set_vehicles(
            vehicles,
            selected_vehicle=selected_vehicle_name,
            allow_empty_selection=True,
        )

        if selected_vehicle_name:

            self.fn_vehicle_changed(
                selected_vehicle_name
            )

            return

        self._current_vehicle = None

        self._update_analyze_state()

    def fn_vehicle_changed(
        self,
        vehicle_name: str,
    ):

        if not vehicle_name:
            self._current_vehicle = None
            self._update_analyze_state()
            return

        self._current_vehicle = self.vehicle_service.load_vehicle(
            vehicle_name
        )

        self._update_analyze_state()

    def fn_log_file_changed(
        self,
        file_path: str,
    ):

        if (
            file_path
            and has_multiple_pt_bo_info_markers(file_path)
        ):

            self.log_selector.set_path("")

            QMessageBox.warning(
                self,
                "Log File Not Supported",
                "The selected log contains multiple PT BO INFO markers. "
                "Please select another diagnostic log.",
            )

        self._update_analyze_state()

    def _update_analyze_state(self):
        if self.log_selector.path():
            self.right_panel.action_panel.fn_set_file_loaded_state()
            return

        self.right_panel.action_panel.fn_set_startup_state()

    def fn_run_clicked(self):
        try:
            result = self.analysis_controller.fn_run(
                log_file=self.log_selector.path(),
                vehicle=self._current_vehicle,
            )

        except ValueError as e:
            QMessageBox.warning(
                self,
                "Analyze",
                str(e),
            )
            return

        except FileNotFoundError as e:
            QMessageBox.warning(
                self,
                "Log File Not Found",
                str(e),
            )
            return

        rows = fn_build_table_rows(
            result["transactions"]
        )

        self.tbl_result.set_data(rows)

        self.right_panel.action_panel.fn_set_analyzed_state()
        self.left_panel.fn_enable_quick_access()

    def fn_export_clicked(self):
        self.export_controller.fn_export(
            parent=self,
            pipeline_result=self.analysis_controller.pipeline_result,
        )

    def fn_copy_clicked(self):
        self.clipboard_controller.fn_copy(
            parent=self,
            log_file=self.log_selector.path(),
        )

    def fn_clear_clicked(self) -> None:
        """Clear current table data and reset analysis UI state."""

        self.tbl_result.clear_data()
        self.filter_box.clear()
        self.pipeline_result = None
        self.analysis_controller.pipeline_result = None
        self.right_panel.action_panel.fn_set_empty_state()
        self.right_panel.action_panel.fn_clear_working_log()
        self.left_panel.fn_disable_quick_access()
        self._update_analyze_state()

    def fn_filter_transactions(self, keyword=None):
        self.tbl_result.fn_search(keyword)

    def fn_quick_filter(self, filter_data: dict):
        self.right_panel.action_panel.fn_set_quick_filter_log(filter_data)
        self.tbl_result.fn_apply_quick_filter(filter_data)

    def fn_refresh_theme(self):
        self.vehicle_selector.fn_refresh_theme()
        self.log_selector.fn_refresh_theme()
        self.right_panel.fn_refresh_theme()
        self.left_panel.fn_refresh_theme()
        self.filter_box.fn_refresh_theme()
        self.tbl_result.fn_refresh_theme()
