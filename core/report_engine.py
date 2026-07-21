from core.view_utils import (
    shorten_text,
    format_timestamp,
    format_response_time,
    format_status,
    format_payload
)

from core.build_transactions import (
    get_final_response_payload
)
"""
Nhóm transaction theo ECU.
Mỗi ECU có summary.
Mỗi ECU có danh sách activities (đã rút gọn, chỉ giữ các trường cần hiển thị).

"""
# TODO: All activities for each ECU
def build_ecu_reports(

    transactions

):

    reports = {}

    for tx in transactions:

        ecu = tx["ecu"]

        if ecu not in reports:

            reports[ecu] = {

                "ecu": ecu,

                "total_transactions": 0,

                "activities": []

            }

        reports[ecu]["total_transactions"] += 1

        reports[ecu]["activities"].append(

            create_activity(tx)

        )

    return reports

# TODO: Display ìnformation expected
def create_activity(transaction):

    activity_name = get_activity_name(transaction)

    response_payload = get_final_response_payload(transaction)

   
    return {

        "timestamp":
            transaction["request"]["timestamp"],

        "display_name": activity_name,

        "service_name":
            transaction["service_name"],

        "identifier":
            transaction["identifier"],

        "identifier_name":
            transaction["identifier_name"],

        "request":
            transaction["request"]["payload"],
        
        "response": response_payload,

        "status":
            transaction["status"],

        "response_time":
            transaction["response_time"],

        "response_pending":
            transaction["response_pending_count"]

    }

def get_activity_name(transaction):

    activity = transaction["display_name"]

    if activity != "UNKNOWN":
        return activity

    if transaction["identifier"]:
        return f"Read DID {transaction['identifier']}"

    if transaction["routine_id"]:
        return f"Routine {transaction['routine_id']}"

    return transaction["service_name"]


# TODO: Chuẩn hóa activity -> TABLE
"""
        Convert ECU report activities to table rows.

        Used by:
            - print_ecu_report()
            - export_ecu_reports_to_excel()
            - GUI Table

        Return:
            [
                {
                    "No": 1,
                    "Time(s)": 0.000,
                    "Service": "READ ECU",
                    "Activity": "Read VIN",
                    "Request": "22 F1 90",
                    "Response": "62 F1 90 ...",
                    "RT(ms)": 1.106,
                    "Status": "PASS"
                },
                ...
            ]
"""

def get_activity_table(report):

    table = []

    for index, activity in enumerate(

        report["activities"],

        start=1

    ):

        response_time = None

        if activity["response_time"] is not None:

            response_time = round(

                activity["response_time"] * 1000,

                3

            )

        table.append(

            {

                "No": index,

                "Time(s)": activity["timestamp"],

                "Service": activity["service_name"],

                "Activity": activity["display_name"],

                "Request": activity["request"],

                "Response": activity["response"],

                "RT(ms)": response_time,

                "Status": activity["status"],

                "Pending": activity["response_pending"]

            }

        )

    return table

# TODO: Thống kê
def calculate_statistics(activities):

    """
    Calculate statistics for one ECU report.

    Parameters
    ----------
    activities : list

    Returns
    -------
    dict
    """

    total = len(activities)

    pass_count = 0

    nrc_only_count = 0

    timeout_count = 0

    pending_count = 0

    response_times = []

    for activity in activities:

        status = activity["status"]

        if status == "OK":

            pass_count += 1

        elif status == "NRC_ONLY":

            nrc_only_count += 1

        elif status == "TIMEOUT":

            timeout_count += 1

        pending_count += activity.get(

            "response_pending",

            0

        )

        response_time = activity.get(

            "response_time"

        )

        if response_time is not None:

            response_times.append(

                response_time * 1000

            )

    pass_rate = 0.0

    if total > 0:

        pass_rate = round(

            pass_count / total * 100,

            2

        )

    average_response_time = None

    max_response_time = None

    if response_times:

        average_response_time = round(

            sum(response_times)

            / len(response_times),

            3

        )

        max_response_time = round(

            max(response_times),

            3

        )

    return {

        "total": total,

        "pass": pass_count,

        "pass_rate": pass_rate,

        "nrc_only": nrc_only_count,

        "timeout": timeout_count,

        "pending_count": pending_count,

        "average_response_time": average_response_time,

        "max_response_time": max_response_time

    }



def print_activity_table(

    table,

    max_rows=10

):

    print("-" * 150)

    print(

        f"{'No':<4}"

        f"{'Time(s)':<10}"

        f"{'Service':<20}"

        f"{'Activity':<30}"

        f"{'Request':<18}"

        f"{'Response':<50}"

        f"{'RT(ms)':>10}"

        f"{'Status':>10}"

    )

    print("-" * 150)

    for row in table[:max_rows]:

        timestamp = format_timestamp(

            row["Time(s)"]

        )

        service = shorten_text(

            row["Service"],

            20

        )

        activity = shorten_text(

            row["Activity"],

            30

        )

        request = format_payload(

            row["Request"],

            18

        )

        response = format_payload(

            row["Response"],

            50

        )

        rt = ""

        if row["RT(ms)"] is not None:

            rt = f"{row['RT(ms)']:.3f}"

        status = format_status(

            row["Status"]

        )

        print(

            f"{row['No']:<4}"

            f"{timestamp:<10}"

            f"{service:<20}"

            f"{activity:<30}"

            f"{request:<18}"

            f"{response:<50}"

            f"{rt:>10}"

            f"{status:>10}"

        )

    if len(table) > max_rows:

        print("-" * 150)

        print(

            f"... ({len(table)-max_rows} more activities)"

        )

# TODO: Helper Print chỉ in tiêu đề + gọi print_activity_table()
def print_ecu_report(

    report,

    max_activities=10

):

    print("=" * 150)

    print(f"ECU                : {report['ecu']}")

    print(f"Total Transactions : {report['total_transactions']}")

    table = get_activity_table(

        report

    )

    print_activity_table(

        table,

        max_activities

    )

    print("=" * 150)


# TODO: Build Summary report
    """
    Build summary information
    for every ECU.

    Return
    ------
    [
        {
            "ECU": "BCM",
            "Total": 108,
            "PASS": 108,
            "NRC_ONLY": 0,
            "TIMEOUT": 0,
            "Average RT(ms)": 1.245,
            "Max RT(ms)": 5.259
        },
        ...
    ]
    """


def build_summary_report(

    ecu_reports

):

    summary = []

    for report in ecu_reports.values():

        statistics = calculate_statistics(

            report["activities"]

        )

        summary.append(

            {

                "ecu": report["ecu"],

                **statistics

            }

        )

    return summary

