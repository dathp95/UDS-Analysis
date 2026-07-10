import pandas as pd

from core.report_engine import (
    get_activity_table,
    build_summary_report
)

# TODO: Export 1 ECU - 1 sheet EXCEL
"""
    Export one ECU report
    to one Excel sheet.

    Parameters
    ----------
    report : dict

    writer : pd.ExcelWriter
"""
def export_ecu_report(

        report,

        writer

        ):
   

    # Chuyen danh sach activity cua 1 ECU thanh bang Excel.
    table = get_activity_table(

        report

    )

    df = pd.DataFrame(

        table

    )

    sheet_name = report["ecu"]

    # Moi ECU duoc ghi vao mot sheet rieng, vi du: MHU, APM, BCM.
    df.to_excel(

        writer,

        sheet_name=sheet_name,

        index=False

    )

# TODO: Export summary sheet 
def export_summary_sheet(

        summary,

        writer

    ):
    # Sheet Summary chua thong ke tong hop cua tat ca ECU.
    df = pd.DataFrame(

        summary

    )

    df.to_excel(

        writer,

        sheet_name="Summary",

        index=False

    )



# TODO: Export All ECU - 1 ECU/1 sheet EXCEL
"""
    Export all ECU reports
    to one workbook.

    Parameters
    ----------
    ecu_reports : dict

    output_file : str
"""
              
def export_workbook(

        summary,

        ecu_reports,

        output_file

    ):

    try: 

        # Tao workbook Excel bang openpyxl engine.
        with pd.ExcelWriter(

            output_file,

            engine="openpyxl"

        ) as writer:

            # Sheet đầu tiên

            export_summary_sheet(

                summary,

                writer

            )

            # Các sheet ECU

            for report in ecu_reports.values():

                # Lap qua tung ECU va tao 1 sheet tuong ung.
                export_ecu_report(

                    report,

                    writer

                )
    except PermissionError:
         # Thuong xay ra khi file Excel dang duoc mo.
         print(

        f"Cannot write '{output_file}'. "

        "Please close the Excel file first."

    )

         return False

    return True
