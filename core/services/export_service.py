"""
    Only manage export folders/files.

        No GUI.

        No Controller.
"""
from pathlib import Path
from datetime import datetime

from config.paths import (
    OUTPUT_DIR,
    REPORT_DIR
)

class ExportService:

    def __init__(self, settings_service):

        self.output_folder = OUTPUT_DIR

        self.settings = settings_service

        self.report_folder = REPORT_DIR

        # self.log_folder = self.output_folder / "Logs"

        # self.temp_folder = self.output_folder / "Temp"

        # self.cache_folder = self.output_folder / "Cache"

        self._fn_create_output_structure()

    # ==========================================
    # Private
    # ==========================================

    def _fn_create_output_structure(self):

        self.output_folder.mkdir(
            exist_ok=True
        )

        self.report_folder.mkdir(
            exist_ok=True
        )

        # self.log_folder.mkdir(
        #     exist_ok=True
        # )

        # self.temp_folder.mkdir(
        #     exist_ok=True
        # )

        # self.cache_folder.mkdir(
        #     exist_ok=True
        # )
    
    def fn_get_report_folder(self) -> Path:

        today = datetime.now().strftime("%d-%m-%Y")

        report_folder = (REPORT_DIR/ today)

        report_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        return report_folder