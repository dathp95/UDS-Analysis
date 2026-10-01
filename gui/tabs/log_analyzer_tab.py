from PySide6.QtCore import Qt, QThread

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QGridLayout,

)

from gui.controllers.analysis_controller import AnalysisController
from gui.controllers.clipboard_controller import ClipboardController
from gui.controllers.report_controller import ReportController
from core.transaction_formatter import fn_build_transaction_rows
from gui.widgets.log_analyzer.filter_box import FilterBox
from gui.widgets.log_analyzer.left_panel import LeftPanel
from gui.widgets.log_analyzer.channel_selector import DiagnosticChannelSelectorWidget
from gui.widgets.log_analyzer.path_selector import PathSelectorWidget
from gui.widgets.log_analyzer.result_table import ResultTable
from gui.widgets.log_analyzer.right_panel import RightPanel
from gui.widgets.vehicle_manager.vehicle_selector import VehicleSelectorWidget
from gui.workers.analysis_worker import AnalysisWorker
from services.vehicle_service import VehicleService
from core.asc_reader import get_log_channels


class LogAnalyzerTab(QWidget):

    def __init__(self):
        super().__init__()

        # Runtime data
        self.pipeline_result = None
        self._current_vehicle = None
        self._analysis_running = False
        self._analysis_thread = None
        self._analysis_worker = None

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

        # ==========================================================
        # Vehicle selector
        # ==========================================================
        self.vehicle_selector = VehicleSelectorWidget()

        # ==========================================================
        # Diagnostic Channel selector
        # ==========================================================
        self.channel_selector = DiagnosticChannelSelectorWidget()

        left_input_layout = QHBoxLayout()
        left_input_layout.setContentsMargins(0, 0, 0, 0)
        left_input_layout.setSpacing(8)

        left_input_layout.addWidget(
            self.vehicle_selector,
            1,
        )

        left_input_layout.addWidget(
            self.channel_selector,
            1,
        )

        # ==========================================================
        # Main layout
        # ==========================================================
        main_layout.setSpacing(8)

        
        

        # ==========================================================
        # Log selector
        # ==========================================================
        self.log_selector = PathSelectorWidget(
            "Log File: Ensure the correct Diagnostic Channel is selected",
            "Log Files (*.blf)",
        )

        # Keep Vehicle / Log File labels at the same height
        input_label_height = max(
            self.vehicle_selector.lbl_vehicle.sizeHint().height(),
            self.channel_selector.lbl_channel.sizeHint().height(),
            self.log_selector.label.sizeHint().height(),
        )

        self.vehicle_selector.lbl_vehicle.setFixedHeight(
            input_label_height
        )

        self.channel_selector.lbl_channel.setFixedHeight(
            input_label_height
        )

        self.log_selector.label.setFixedHeight(
            input_label_height
        )

        # ==========================================================
        # Main widgets
        # ==========================================================
        self.filter_box = FilterBox()

        self.left_panel = LeftPanel()
        self.tbl_result = ResultTable()
        self.right_panel = RightPanel()

        # Quick Filter search is created inside QuickAccessWidget
        # but displayed in the main grid.
        self.quick_filter_search = (
            self.left_panel.quick_access.edit_search
        )

        # ==========================================================
        # Top input layout
        # ==========================================================
       

        # ==========================================================
        # Search + Content Grid
        #
        # Column 0 = Quick Filter
        # Column 1 = Result Table
        # Column 2 = Right Panel
        #
        # Using the SAME grid guarantees vertical alignment.
        # ==========================================================
        content_grid = QGridLayout()

        content_grid.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        content_grid.setHorizontalSpacing(8)
        content_grid.setVerticalSpacing(8)

        # ----------------------------------------------------------
        # Column ratio
        # Left : Table : Right
        #   5  :  18   :   4
        # ----------------------------------------------------------
        content_grid.setColumnStretch(0, 6)
        content_grid.setColumnStretch(1, 16)
        content_grid.setColumnStretch(2, 5)

        # ==========================================================
        # Row 0 - Search
        # ==========================================================
        content_grid.addLayout(
            left_input_layout,
            0,
            0,
        )
        
        content_grid.addWidget(
            self.log_selector,
            0,
            1,
        )
        content_grid.addWidget(
            self.quick_filter_search,
            1,
            0,
        )

        content_grid.addWidget(
            self.filter_box,
            1,
            1,
        )

        # Column 2 intentionally empty.
        # This keeps Search ECU aligned exactly with Result Table.

        # ==========================================================
        # Row 1 - Main content
        # ==========================================================
        content_grid.addWidget(
            self.left_panel,
            2,
            0,
        )

        content_grid.addWidget(
            self.tbl_result,
            2,
            1,
        )

        content_grid.addWidget(
            self.right_panel,
            0,
            2,
            3,
            1,
        )

        # Search row only uses required height.
        # Main content consumes remaining vertical space.
        content_grid.setRowStretch(0, 0)
        content_grid.setRowStretch(1, 0)
        content_grid.setRowStretch(2, 1)

        # ==========================================================
        # Add everything to main layout
        # ==========================================================
        

        main_layout.addLayout(
            content_grid,
            1,
        )

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

        self.channel_selector.channel_changed.connect(
            self._update_analyze_state
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

        self.left_panel.quick_filter_cleared.connect(
            self.right_panel.action_panel.fn_clear_quick_filter_info
        )

        self.tbl_result.cellClicked.connect(
            self._fn_result_row_selected
        )

        self.tbl_result.transaction_selected.connect(
            self.right_panel.action_panel.fn_set_transaction_info
        )

        self.tbl_result.create_quick_filter_requested.connect(
            self._fn_create_quick_filter_from_transaction
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

        self.channel_selector.fn_clear()

        if not file_path:
            self._update_analyze_state()
            return

        try:
            channels = get_log_channels(file_path)

        except (OSError, ValueError) as e:
            self.channel_selector.fn_set_channels([])

            QMessageBox.warning(
                self,
                "Log File",
                str(e),
            )

            self._update_analyze_state()
            return

        self.channel_selector.fn_set_channels(channels)

        if not channels:
            QMessageBox.warning(
                self,
                "Log File",
                "No CAN channel detected in the selected log.",
            )

        self._update_analyze_state()

    def _update_analyze_state(self):
        if self._analysis_running:
            self.right_panel.action_panel.fn_set_analysis_started()
            return

        if (
            self.log_selector.path()
            and self._current_vehicle is not None
            and self.channel_selector.fn_channel() is not None
        ):
            self.right_panel.action_panel.fn_set_file_loaded_state()
            return

        self.right_panel.action_panel.fn_set_startup_state()

    def _fn_set_analysis_inputs_enabled(
        self,
        enabled: bool,
    ):
        self.vehicle_selector.setEnabled(enabled)
        self.channel_selector.setEnabled(enabled)
        self.log_selector.setEnabled(enabled)

    def fn_run_clicked(self):
        if self._analysis_running:
            return

        log_file = self.log_selector.path()
        vehicle = self._current_vehicle
        channel = self.channel_selector.fn_channel()

        self._analysis_running = True
        self._fn_set_analysis_inputs_enabled(False)
        self.right_panel.action_panel.fn_set_analysis_started()
        self._fn_start_analysis_thread(
            log_file,
            vehicle,
            channel,
        )

    def _fn_start_analysis_thread(
        self,
        log_file: str,
        vehicle,
        channel,
    ):
        self._analysis_thread = QThread(self)
        self._analysis_worker = AnalysisWorker(
            controller=self.analysis_controller,
            log_file=log_file,
            vehicle=vehicle,
            channel=channel,
        )
        self._analysis_worker.moveToThread(
            self._analysis_thread
        )

        self._analysis_thread.started.connect(
            self._analysis_worker.run
        )
        self._analysis_worker.status_changed.connect(
            self.right_panel.action_panel.fn_set_analysis_status
        )
        self._analysis_worker.finished.connect(
            self._fn_analysis_finished
        )
        self._analysis_worker.failed.connect(
            self._fn_analysis_failed
        )
        self._analysis_worker.finished.connect(
            self._analysis_thread.quit
        )
        self._analysis_worker.failed.connect(
            self._analysis_thread.quit
        )
        self._analysis_thread.finished.connect(
            self._analysis_worker.deleteLater
        )
        self._analysis_thread.finished.connect(
            self._analysis_thread.deleteLater
        )
        self._analysis_thread.finished.connect(
            self._fn_analysis_thread_finished
        )

        self._analysis_thread.start()

    def _fn_analysis_finished(
        self,
        result,
    ):
        self._analysis_running = False
        self._fn_set_analysis_inputs_enabled(True)
        self.pipeline_result = result
        self.analysis_controller.pipeline_result = result

        rows = fn_build_transaction_rows(
            result["transactions"]
        )

        self.tbl_result.set_data(rows)
        self.tbl_result.clearSelection()
        self.tbl_result.setCurrentCell(-1, -1)
        self.right_panel.action_panel.fn_clear_transaction_info()

        self.right_panel.action_panel.fn_set_analysis_completed()
        self.right_panel.action_panel.fn_set_analyzed_state()
        self.left_panel.fn_enable_quick_access()

    def _fn_analysis_failed(
        self,
        message: str,
    ):
        self._analysis_running = False
        self._fn_set_analysis_inputs_enabled(True)
        self._update_analyze_state()
        self.right_panel.action_panel.fn_set_analysis_failed(message)

        QMessageBox.warning(
            self,
            "Analyze",
            message,
        )

    def _fn_analysis_thread_finished(self):
        self._analysis_thread = None
        self._analysis_worker = None

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
        self.right_panel.action_panel.fn_set_analysis_ready()
        
        self.right_panel.action_panel.fn_set_empty_state()
        self.right_panel.action_panel.fn_clear_detail_panels()
        self.left_panel.fn_disable_quick_access()
        self._update_analyze_state()

    def fn_filter_transactions(self, keyword=None):
        self.tbl_result.fn_search(keyword)

    def fn_quick_filter(self, filter_data: dict):
        self.right_panel.action_panel.fn_set_quick_filter_info(filter_data)
        self.tbl_result.fn_apply_quick_filter(filter_data)

    def _fn_result_row_selected(
        self,
        row: int,
        column: int,
    ):
        self.right_panel.action_panel.fn_set_transaction_info(
            self.tbl_result.fn_row_data(row)
        )

    def _fn_create_quick_filter_from_transaction(
        self,
        row_data: dict,
    ):
        self.left_panel.quick_access.fn_create_from_transaction(
            row_data
        )

    def fn_refresh_theme(self):
        self.vehicle_selector.fn_refresh_theme()
        self.channel_selector.fn_refresh_theme()
        self.log_selector.fn_refresh_theme()
        self.right_panel.fn_refresh_theme()
        self.left_panel.fn_refresh_theme()
        self.filter_box.fn_refresh_theme()
        self.tbl_result.fn_refresh_theme()
