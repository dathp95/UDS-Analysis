
from core.pipeline import run_pipeline

from core.report_export import export_workbook

class MainController:
    def __init__(self):
        pass

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
        

    
    
    
