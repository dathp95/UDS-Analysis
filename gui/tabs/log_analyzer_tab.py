from PySide6.QtCore import Qt

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

        # ==========================================================
        # Main layout
        # ==========================================================
        main_layout.setSpacing(8)

        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)

        # ==========================================================
        # Vehicle selector
        # ==========================================================
        self.vehicle_selector = VehicleSelectorWidget()

        # ==========================================================
        # Log selector
        # ==========================================================
        self.log_selector = PathSelectorWidget(
            "Log File: Supported logs Diagnostic only - NO: PT, CH, BO, IF...",
            "Log Files (*.blf *.asc)",
        )

        # Keep Vehicle / Log File labels at the same height
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
        content_grid.addWidget(
            self.quick_filter_search,
            0,
            0,
        )

        content_grid.addWidget(
            self.filter_box,
            0,
            1,
        )

        # Column 2 intentionally empty.
        # This keeps Search ECU aligned exactly with Result Table.

        # ==========================================================
        # Row 1 - Main content
        # ==========================================================
        content_grid.addWidget(
            self.left_panel,
            1,
            0,
        )

        content_grid.addWidget(
            self.tbl_result,
            1,
            1,
        )

        content_grid.addWidget(
            self.right_panel,
            1,
            2,
        )

        # Search row only uses required height.
        # Main content consumes remaining vertical space.
        content_grid.setRowStretch(0, 0)
        content_grid.setRowStretch(1, 1)

        # ==========================================================
        # Add everything to main layout
        # ==========================================================
        main_layout.addLayout(
            input_layout
        )

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
        self.tbl_result.clearSelection()
        self.tbl_result.setCurrentCell(-1, -1)
        self.right_panel.action_panel.fn_clear_transaction_info()

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
        self.log_selector.fn_refresh_theme()
        self.right_panel.fn_refresh_theme()
        self.left_panel.fn_refresh_theme()
        self.filter_box.fn_refresh_theme()
        self.tbl_result.fn_refresh_theme()

