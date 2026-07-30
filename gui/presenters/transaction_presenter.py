

from core.build_transactions import get_final_response_payload


def fn_build_table_rows(transactions):


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

        rows.append({

            "ECU": tx.get("ecu", ""),

            "Time": request.get("timestamp", ""),

            "Activity": tx.get("display_name", ""),

            "Request": request.get("payload", ""),

            "Response": response_payload,

            "RT (ms)": rt_ms,

            "Status": tx.get("status", "")

        })

    return rows
