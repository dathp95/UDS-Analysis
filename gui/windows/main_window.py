from datetime import datetime

from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QFileDialog
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QMessageBox,
    QPushButton,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog
)

from gui.widgets.path_selector import PathSelectorWidget

from gui.controllers.main_controllers import MainController

from gui.widgets.panels.action_panel import ActionPanel

from gui.widgets.result_table import ResultTable

from gui.presenters.transaction_presenter import (
    fn_build_table_rows
)

from gui.widgets.filter_box import FilterBox

from gui.widgets.right_panel import RightPanel

from gui.themes.styles.containers.window_style import (
    fn_window_style
)

from gui.themes.theme_manager import ThemeManager

from gui.themes.styles.containers.window_style import (
    fn_window_style
)

from gui.controllers.export_controller import (
    ExportController
)



class MainWindow(QMainWindow):   

    def __init__(self):
        super().__init__()

        # Window properties
        self.setWindowTitle("Python UDS Analyzer")
        self.resize(1200, 700)

        # Controllers
        self._create_controllers()

        # Luu ket qua sau khi bam RUN, dung lai khi EXPORT ra Excel.
        self.pipeline_result = None

        # Build UI
        self.setup_ui()

        # Connect signals
        self._connect_signals()

        # Initial UI state
        self.right_panel.action_panel.fn_set_startup_state()

        # Apply theme
        self.fn_refresh_theme()


        
       

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        content_layout = QHBoxLayout()
        
        central_widget.setLayout(main_layout)
        
        self.log_selector = PathSelectorWidget(
            "Log File",
            "Log Files (*.blf *.asc)"
        )

        self.filter_box = FilterBox()

    
        self.tbl_result = ResultTable()
        self.right_panel = RightPanel()

        content_layout.addWidget(self.tbl_result, 4)
        content_layout.addWidget(self.right_panel, 1)

        main_layout.addWidget(self.log_selector)
        main_layout.addWidget(self.filter_box)
        
        main_layout.addLayout(content_layout)     

    def _create_controllers(self):

        self.main_controller = MainController()

        self.export_controller = ExportController()
    
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

        # Nut CLEAR xoa du lieu hien tai tren bang ket qua.
        self.right_panel.action_panel.clear_clicked.connect(
            self.fn_clear_clicked
        )
        

        self.right_panel.theme_switch.theme_changed.connect(

            self.fn_change_theme

            )

    def fn_log_file_changed(
            self,
            file_path: str
        ):

        print(file_path)

        self.right_panel.action_panel.fn_set_file_loaded_state() 
    
    
        
    def fn_run_clicked(self):
        log_file = self.log_selector.path()

        # Chay pipeline phan tich log va giu ket qua de hien thi/export.
        result = self.main_controller.fn_analyze_log(
            log_file= log_file,
            ecu_config="config/ecu_config.xlsx",
        )

        self.pipeline_result = result

        transactions = result["transactions"]

        rows = fn_build_table_rows(transactions)

        self.tbl_result.set_data(rows)

        self.right_panel.action_panel.fn_set_analyzed_state()
    
    def fn_export_clicked(self):
        print("Export Clicked")

        # Chi cho phep export sau khi da RUN va co pipeline_result.
        if not self.pipeline_result:
            QMessageBox.warning(
                self,
                "Export",
                "Please run analysis before exporting."
            )
            return

        # Tao ten file mac dinh: Summary_ngay-thang-nam.xlsx.
        export_folder = self.export_controller.fn_prepare_export()
        today = datetime.now().strftime("%d-%m-%Y")
        default_file = export_folder / f"Summary_{today}.xlsx"

        # Mo cua so de nguoi dung chon thu muc va ten file Excel.
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel Report",
            str(default_file),
            "Excel Files (*.xlsx)"
        )

        if not output_file:
            return

        if not output_file.lower().endswith(".xlsx"):
            output_file = f"{output_file}.xlsx"

        try:
            # Ghi workbook: sheet Summary + moi ECU la mot sheet rieng.
            exported = self.main_controller.fn_export_report(
                pipeline_result=self.pipeline_result,
                output_file=output_file
            )

            if exported:
                QMessageBox.information(
                    self,
                    "Export",
                    f"Excel report saved:\n{output_file}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Export",
                    "Cannot write the Excel file. Please close it and try again."
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Export Error",
                str(error)
            )


    def fn_clear_clicked(self):
        # Xoa data tren bang va reset filter/ket qua phan tich hien tai.
        self.tbl_result.clear_data()
        self.filter_box.clear()
        self.pipeline_result = None
        self.right_panel.action_panel.fn_set_empty_state()
    
    
    def fn_filter_transactions(self, keyword = None):

        self.tbl_result.fn_filter(keyword)
    
    def fn_change_theme(self,theme):
           
        ThemeManager.fn_set_theme(theme)
        self.fn_refresh_theme()
    
    def fn_refresh_theme(self):

        self.setStyleSheet(

            fn_window_style()

        )
        self.log_selector.fn_refresh_theme()

        self.right_panel.fn_refresh_theme()

        self.filter_box.fn_refresh_theme()

        self.tbl_result.fn_refresh_theme()
            
    


        

        

      
