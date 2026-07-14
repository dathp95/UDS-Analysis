from PySide6.QtWidgets import QMessageBox

from core.services.report_service import ReportService


class ReportController:

    def __init__(self):

        self.report_service = ReportService()

    # ==========================================
    # Public
    # ==========================================

    def fn_export(
        self,
        parent,
        pipeline_result
    ):

        if pipeline_result is None:

            QMessageBox.warning(

                parent,

                "Export",

                "Please run analysis before exporting."

            )

            return

        try:

            output_file = self.report_service.fn_export(

                parent=parent,

                pipeline_result=pipeline_result

            )

            if output_file is None:

                return

            QMessageBox.information(

                parent,

                "Export",

                f"Excel report saved:\n\n{output_file}"

            )

        except Exception as error:

            QMessageBox.critical(

                parent,

                "Export Error",

                str(error)

            )