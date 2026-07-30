import pandas as pd

from core.build_transactions import get_final_response_payload


def export_transactions_to_excel(
    transactions,
    output_file="transactions.xlsx"
):

    rows = []

    for tx in transactions:

        request_payload = tx[
            "request"
        ]["payload"]

        response_payload = get_final_response_payload(tx)

        if request_payload == "22 F1 68":

            print()

            print(
                "EXPORT DEBUG"
            )

            print(
                "REQ:",
                request_payload
            )

            print(
                "POS:",
                response_payload
            )

        rows.append({

            "ECU":
            tx["ecu"],

            "Status": tx["status"],

            "Request":
            request_payload,

            "NRC Count":
            len(
                tx["negative_responses"]
            ),

            "Response":
            response_payload,

            "Response Time (s)":
            tx["response_time"]

        })

    df = pd.DataFrame(
        rows
    )

    print(df[
    df["Request"] == "22 F1 68"
    ])

    df.to_excel(
        output_file,
        index=False
    )

    print(
        f"Saved: {output_file}"
    )

# def export_transactions_to_excel():
