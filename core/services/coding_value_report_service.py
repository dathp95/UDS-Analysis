from __future__ import annotations

from datetime import datetime
from pathlib import Path

from config.paths import CODING_VALUE_REPORT_DIR
from core.coding_value_report_export import (
    CodingValueReportData,
    export_coding_value_report,
)


class CodingValueReportService:
    def __init__(
            self,
            report_root: str | Path | None = None,
            exporter=export_coding_value_report,
            now_provider=datetime.now,
        ):
        self.report_root = (
            Path(report_root)
            if report_root is not None
            else CODING_VALUE_REPORT_DIR
        )
        self._exporter = exporter
        self._now_provider = now_provider

    def report_folder(self) -> Path:
        today = self._now_provider().strftime("%d-%m-%Y")
        report_folder = self.report_root / today
        report_folder.mkdir(parents=True, exist_ok=True)
        return report_folder

    def default_report_path(self) -> Path:
        now = self._now_provider()
        return self.report_folder() / (
            f"EEIV_report_Coding value_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

    def export_report(
            self,
            report_data: CodingValueReportData,
            output_file: str | Path,
        ) -> Path:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        exported_path = self._exporter(report_data, output_path)
        return Path(exported_path)
