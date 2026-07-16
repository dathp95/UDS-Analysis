from core.pipeline import run_pipeline


class AnalysisController:

    def __init__(self):

        self.pipeline_result = None

    # ==========================================
    # Public
    # ==========================================

    def fn_run(
        self,
        log_file: str,
        ecu_config: str,
    ):

        

        result = run_pipeline(

            asc_file=log_file,

            ecu_config=ecu_config

        )

        self.pipeline_result = result

        return result