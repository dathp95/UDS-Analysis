import pandas as pd


def export_transactions_to_excel(
    transactions,
    output_file="transactions.xlsx"
):

    rows = []

    for tx in transactions:

        request_payload = tx[
            "request"
        ]["payload"]

        positive_payload = ""

        if tx["positive_response"]:

            positive_payload = tx[
                "positive_response"
            ]["payload"]

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
                positive_payload
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

            "Positive Response":
            positive_payload,

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