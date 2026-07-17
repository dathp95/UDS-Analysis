import pandas as pd

from core.report_engine import (
    get_activity_table,
)
from gui.presenters.transaction_presenter import fn_build_table_rows

# ==========================================================
# Private
# ==========================================================

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

    df.to_excel(
        writer,
        sheet_name=report["ecu"],
        index=False,
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