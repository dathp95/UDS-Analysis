import csv
from io import StringIO

from core.build_transactions import get_final_response_payload


TRANSACTION_COLUMNS = ("ECU", "Time", "Activity", "Request", "Response", "RT (ms)", "Status")


def fn_build_transaction_rows(transactions):
    rows = []

    for tx in transactions:
        request = tx.get("request") or {}
        response_payload = get_final_response_payload(tx)
        response_time = tx.get("response_time")
        rt_ms = (
            round(response_time * 1000, 2)
            if response_time is not None
            else ""
        )

        rows.append(dict(zip(TRANSACTION_COLUMNS, (
            tx.get("ecu", ""),
            request.get("timestamp", ""),
            tx.get("display_name", ""),
            request.get("payload", ""),
            response_payload,
            rt_ms,
            tx.get("status", ""),
        ), strict=True)))

    return rows


def fn_format_transaction_rows_tsv(rows):
    """Serialize already formatted rows using the ALL_ECUS column contract."""
    def cell_text(value):
        if value is None:
            return ""
        return (str(value).replace("\r\n", " ").replace("\r", " ")
                .replace("\n", " ").replace("\t", " "))

    output = StringIO(newline="")
    writer = csv.writer(output, dialect="excel-tab")
    writer.writerow(TRANSACTION_COLUMNS)
    writer.writerows([cell_text(row.get(column, "")) for column in TRANSACTION_COLUMNS]
                     for row in rows)
    return output.getvalue()
