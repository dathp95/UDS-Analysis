from core.asc_reader import (
    load_log,
    extract_negative_responses,
    reassemble_isotp,
    extract_positive_responses,
    extract_requests,
)

from core.build_transactions import (
    build_transactions_v4,
)

from core.ecu_mapping import (
    load_vehicle_mapping,
)

from core.uds_lookup import (
    get_positive_response_timeout,
)

from core.report_engine import (
    build_ecu_reports,
    build_summary_report,
)


def run_pipeline(
        asc_file: str,
        vehicle,
        logger=None,
        progress_callback=None,
        channel=None,
    ):

    # ==========================================
    # Load Files
    if logger:
        if channel is None:
            logger("Reading log...")
        else:
            logger(f"Reading Channel {channel}...")

    messages = load_log(asc_file, channel=channel)

    if logger:
        logger("Loading vehicle configuration...")

    ecu_info, req_map, resp_map = load_vehicle_mapping(vehicle)

    if not ecu_info:
        raise ValueError(
            "Selected vehicle does not have any ECU with request and response IDs."
        )

    # ==========================================
    # Parse UDS
    if logger:
        logger("Parsing ISO-TP / UDS...")

    completed_payloads = reassemble_isotp(messages)
    requests = extract_requests(messages, completed_payloads)
    negative_responses = extract_negative_responses(messages)
    positive_responses = extract_positive_responses(completed_payloads)

    # ==========================================
    # Build Transactions
    if logger:
        logger("Building Transactions...")

    transactions = build_transactions_v4(
        requests,
        positive_responses,
        negative_responses,
        ecu_info,
        timeout=get_positive_response_timeout()
    )

    # ==========================================
    # Debug
    if logger:
        logger(f"Transactions : {len(transactions)}")

    # ==========================================
    # Report
    if logger:
        logger("Generating analysis result...")

    ecu_reports = build_ecu_reports(transactions)
    summary = build_summary_report(ecu_reports)

    if logger:
        logger("Completed")

    return {
        "summary": summary,
        "ecu_reports": ecu_reports,
        "transactions": transactions
    }
