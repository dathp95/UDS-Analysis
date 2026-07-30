from pathlib import Path
from core.pipeline import run_pipeline
from models.vehicle import Vehicle


class AnalysisController:

    def __init__(self):
        self.pipeline_result = None

    def fn_run(
            self,
            log_file: str,
            vehicle: Vehicle,
        ):
    
        if not log_file:
            raise ValueError(
                "Please select a Diagnostic CAN log (.asc or .blf) before running the analysis."
            )

        if vehicle is None:
            raise ValueError(
                "Please select a vehicle before running the analysis."
            )

        if not Path(log_file).is_file():
            raise FileNotFoundError(
                "The selected log file could not be found."
            )

        result = run_pipeline(

            asc_file=log_file,

            vehicle=vehicle

        )

        self.pipeline_result = result

        return result
