from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox
    
)


from gui.controllers.analysis_controller import AnalysisController
from gui.controllers.report_controller import ReportController
from gui.controllers.clipboard_controller import ClipboardController

from gui.presenters.transaction_presenter import (
    fn_build_table_rows,
)

from gui.themes.icon_manager import IconManager
from gui.themes.theme_manager import ThemeManager
from gui.themes.styles.containers.window_style import (
    fn_window_style,
)

from gui.widgets.filter_box import FilterBox
from gui.widgets.path_selector import PathSelectorWidget
from gui.widgets.result_table import ResultTable
from gui.widgets.right_panel import RightPanel
from gui.widgets.left_panel import LeftPanel

from PySide6.QtGui import QIcon
from gui.themes.icon_manager import IconManager

from config.paths import CONFIG_DIR

class MainWindow(QMainWindow):   

    def __init__(self):
        super().__init__()

        # Window properties
        self.setWindowTitle(" V-CODE v1.0.0 | AES EEIV by DAT TRAN")
        self.setWindowIcon(
            IconManager.app()
        )
        
        self.resize(1200, 800)

        # Runtime data
        self.pipeline_result = None

        # Controllers
        self._create_controllers()    

        # Build UI
        self.setup_ui()

        # Connect signals
        self._connect_signals()

        # Initial UI state
        self.right_panel.action_panel.fn_set_startup_state()
        self.left_panel.fn_disable_quick_access()
        
        # # Apply theme

        self.fn_refresh_theme()


        
       

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        content_layout = QHBoxLayout()
        
        central_widget.setLayout(main_layout)
        
        self.log_selector = PathSelectorWidget(
            "Log File: Supported logs Diagnostic only - NO: PT, CH, BO, IF...",
            "Log Files (*.blf *.asc)"
        )
        

        self.filter_box = FilterBox()

        self.left_panel = LeftPanel()
        self.tbl_result = ResultTable()
        self.right_panel = RightPanel()

        content_layout.addWidget(self.left_panel,3)
        content_layout.addWidget(self.tbl_result, 7)
        content_layout.addWidget(self.right_panel, 2)

        main_layout.addWidget(self.log_selector)
        main_layout.addWidget(self.filter_box)
        
        main_layout.addLayout(content_layout)     

    def _create_controllers(self):

        self.analysis_controller = AnalysisController()

        self.export_controller = ReportController()

        self.clipboard_controller = ClipboardController()


    def _connect_signals(self):

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

        # Nut COPY dua toan bo noi dung file ASC vao clipboard.
        self.right_panel.action_panel.copy_clicked.connect(
            self.fn_copy_clicked
        )

        # Nut CLEAR xoa du lieu hien tai tren bang ket qua.
        self.right_panel.action_panel.clear_clicked.connect(
            self.fn_clear_clicked
        )
        
        self.left_panel.quick_filter_selected.connect(

            self.fn_quick_filter

        )

        self.left_panel.theme_switch.theme_changed.connect(

            self.fn_change_theme

            )

    def fn_log_file_changed(
            self,
            file_path: str
        ):

        self.right_panel.action_panel.fn_set_file_loaded_state() 
    
    
        

    def fn_run_clicked(self):

        try:

            result = self.analysis_controller.fn_run(

                log_file=self.log_selector.path(),

                ecu_config=CONFIG_DIR / "ecu_config.xlsx"

            )

        except ValueError as e:

            QMessageBox.warning(
                self,
                "No Log Selected",
                str(e)
            )
            return

        except FileNotFoundError as e:

            QMessageBox.warning(
                self,
                "Log File Not Found",
                str(e)
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

            pipeline_result=self.analysis_controller.pipeline_result
        )

    def fn_copy_clicked(self):

        self.clipboard_controller.fn_copy(
            parent=self,
            log_file=self.log_selector.path()
        )



    def fn_clear_clicked(self) -> None:
        """Clear current table data and reset analysis UI state.

        This slot is connected to the CLEAR button. It only resets the current
        UI result view and cached pipeline result.
        """
        self.tbl_result.clear_data()
        self.filter_box.clear()
        self.pipeline_result = None
        self.right_panel.action_panel.fn_set_empty_state()

        self.left_panel.fn_disable_quick_access()
    
    
    def fn_filter_transactions(self, keyword = None):

        self.tbl_result.fn_search(keyword)

    def fn_quick_filter(self, filter_data: dict,):

        self.tbl_result.fn_apply_quick_filter(filter_data)
    
   
    
    
    def fn_change_theme(self,theme):
           
        ThemeManager.fn_set_theme(theme)
        self.fn_refresh_theme()
    
    def fn_refresh_theme(self):

        self.setStyleSheet(

            fn_window_style()

        )
        self.log_selector.fn_refresh_theme()

        self.right_panel.fn_refresh_theme()
        self.left_panel.fn_refresh_theme()

        self.filter_box.fn_refresh_theme()

        self.tbl_result.fn_refresh_theme()
            
    


        

        

      
