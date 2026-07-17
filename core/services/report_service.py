from pathlib import Path
from datetime import datetime
from config.paths import REPORT_DIR
from PySide6.QtWidgets import QFileDialog

from core.report_export import export_workbook


class ReportService:

    def __init__(self):

        pass

    # ==========================================
    # Public
    # ==========================================

    def fn_export(

            self,

            parent,

            pipeline_result

        ):

        

        output_file = self.fn_choose_output_file(parent)

        if output_file is None:

            return None

        success = export_workbook(

            summary=pipeline_result["summary"],

            ecu_reports=pipeline_result["ecu_reports"],
            
            transactions=pipeline_result["transactions"],

            output_file=output_file

        )
        if not success:
            return None

        return output_file
    
    
    def fn_choose_output_file(

            self,

            parent

        ):

        report_folder = self.fn_get_report_folder()

        timestamp = datetime.now().strftime(

            "%Y%m%d_%H%M%S"

        )

        default_name = (

            f"EEIV_ecu_reports_{timestamp}.xlsx"

        )

        default_path = report_folder / default_name

        output_file, _ = QFileDialog.getSaveFileName(

            parent,

            "Save Excel Report",

            str(default_path),

            "Excel Files (*.xlsx)"

        )

        if not output_file:

            return None

        if not output_file.lower().endswith(".xlsx"):

            output_file += ".xlsx"

        return output_file
    

    def fn_get_report_folder(self):

        today = datetime.now().strftime(

            "%d-%m-%Y"

        )

        report_folder = (REPORT_DIR / today)

        report_folder.mkdir(

            parents=True,

            exist_ok=True

        )

        return report_folder