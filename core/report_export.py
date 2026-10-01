import pandas as pd

from core.excel_styles import (
    HEADER_ALIGNMENT,
    HEADER_FILL,
    HEADER_FONT,
    THIN_BORDER,
)
from core.report_engine import (
    get_activity_table,
)
from gui.presenters.transaction_presenter import fn_build_table_rows

# ==========================================================
# Private
# ==========================================================


def _format_table_sheet(
        writer,
        sheet_name: str,
    ):
    sheet = writer.sheets[sheet_name]

    for cell in sheet[1]:
        cell.font = HEADER_FONT
        cell.alignment = HEADER_ALIGNMENT
        cell.fill = HEADER_FILL
        cell.border = THIN_BORDER

    for row in sheet.iter_rows(
        min_row=2,
        max_row=sheet.max_row,
        min_col=1,
        max_col=sheet.max_column,
    ):
        for cell in row:
            cell.border = THIN_BORDER

    sheet.freeze_panes = "A2"

    if sheet.max_column > 0:
        sheet.auto_filter.ref = sheet.dimensions

def _export_summary_sheet(
        summary,
        writer,
    ):
    
    """
    Export summary information
    to the Summary worksheet.
    """

    df = pd.DataFrame(summary)

    df.to_excel(
        writer,
        sheet_name="Summary",
        index=False,
    )

    _format_table_sheet(
        writer,
        "Summary",
    )


def _export_ecu_report(
    report,
    writer,
):
    """
    Export one ECU report
    to one worksheet.
    """

    table = get_activity_table(report)

    df = pd.DataFrame(table)

    sheet_name = _safe_sheet_name(report["ecu"])

    df.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
    )

    _format_table_sheet(
        writer,
        sheet_name,
    )


# ==========================================================
# Public
# ==========================================================

def export_workbook(
    summary,
    ecu_reports,
    transactions,
    output_file,
):
    """
    Export all ECU reports
    to one Excel workbook.

    Workbook structure

    Summary
    BCM
    MHU
    APM
    ...
    """

    try:

        with pd.ExcelWriter(
            output_file,
            engine="openpyxl",
        ) as writer:

            _export_summary_sheet(
                summary,
                writer,
            )
            _export_all_ecus(
                transactions,
                writer,
            )


            for report in ecu_reports.values():

                _export_ecu_report(
                    report,
                    writer,
                )
            
            

    except PermissionError:

        return False

    return True


def _export_all_ecus(
    transactions,
    writer,
):

    rows = fn_build_table_rows(
        transactions
    )

    df = pd.DataFrame(rows)

    df.to_excel(
        writer,
        sheet_name="ALL_ECUS",
        index=False,
    )

    _format_table_sheet(
        writer,
        "ALL_ECUS",
    )


def _safe_sheet_name(name: str) -> str:
    r"""
    Excel worksheet name:
    - max 31 chars
    - cannot contain : \ / ? * [ ]
    """

    invalid_chars = r'[]:*?/\\'

    for ch in invalid_chars:
        name = name.replace(ch, "_")

    return name[:31]