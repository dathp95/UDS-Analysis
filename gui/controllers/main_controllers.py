
from core.pipeline import run_pipeline

from core.report_export import export_workbook
from core.services.copy_service import CopyService


class MainController:

    # ==========================================================================
    # Function: __init__
    #
    # Purpose:
    #     Initialize controller dependencies.
    #
    # Inputs:
    #     self: MainController instance.
    #
    # Outputs:
    #     None.
    #
    # Called by:
    #     MainWindow._create_controllers()
    #
    # Calls:
    #     CopyService()
    #
    # Side Effects:
    #     Creates service instances used by controller workflows.
    #
    # Responsibility:
    #     Prepare controller-level dependencies.
    #
    # Does NOT:
    #     - Run analysis.
    #     - Read ASC files.
    #     - Export Excel.
    #     - Update GUI.
    #     - Parse UDS transactions.
    #
    # ==========================================================================
    def __init__(self) -> None:
        """Initialize services used by main controller workflows."""
        self.copy_service = CopyService()

    def fn_analyze_log(
            self, 
            log_file: str, 
            ecu_config: str,
            ):
        
        print("[MainController] Analyze Started")
        print(f"[MainController] Log File : {log_file}")

        result = run_pipeline(
            asc_file =  log_file,
            ecu_config  =   ecu_config,
        )

        # print(result["transactions"][0])
        

        return result
    
    def fn_export_report(
                self,
                pipeline_result,
                output_file: str
        ):

        # Chuyen ket qua pipeline sang tang export de tao file Excel.
        # Workbook gom sheet Summary va cac sheet ECU rieng le.
        return export_workbook(
            summary = pipeline_result["summary"],
            ecu_reports = pipeline_result["ecu_reports"],
            output_file = output_file
        )

    # ==========================================================================
    # Function: fn_get_copy_content
    #
    # Purpose:
    #     Coordinate the copy workflow for selected ASC log content.
    #
    # Inputs:
    #     log_file: Selected ASC or BLF log file path.
    #
    # Outputs:
    #     tuple[str, str]: Resolved ASC file path and ASC text content.
    #
    # Called by:
    #     MainWindow.fn_copy_clicked()
    #
    # Calls:
    #     CopyService.fn_read_asc_content()
    #
    # Side Effects:
    #     Delegates file reading to CopyService.
    #
    # Responsibility:
    #     Coordinate copy data retrieval between GUI and service layer.
    #
    # Does NOT:
    #     - Update GUI.
    #     - Write to clipboard.
    #     - Parse BLF or UDS data.
    #     - Build transactions.
    #     - Export Excel.
    #
    # ==========================================================================
    def fn_get_copy_content(self, log_file: str) -> tuple[str, str]:
        """Get ASC content for the GUI clipboard action.

        Args:
            log_file: Selected log file path from the GUI.

        Returns:
            A tuple containing resolved ASC file path and text content.
        """
        return self.copy_service.fn_read_asc_content(log_file)
        

    
    
    
