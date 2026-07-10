


from core.asc_reader import (
    load_log,    
    extract_negative_responses,
    reassemble_isotp,
    extract_positive_responses,
    extract_requests
)

from core.build_transactions import (
    build_transactions_v4
)


from core.ecu_mapping import (
    load_ecu_mapping
)

from core.uds_lookup import (
    POSITIVE_RESPONSE_TIMEOUT
)

from core.report_engine import (
    build_ecu_reports,
    get_activity_table,
    print_activity_table,
    print_ecu_report,
    build_summary_report
)

from core.export_transactions import (
    export_transactions_to_excel
)

from core.report_export import export_workbook






def run_pipeline(
        asc_file : str,
        ecu_config: str,
        logger=None,
        progress_callback=None

    ):

    # ==========================================
    # Load Files
    messages = load_log(asc_file)

    
    if logger:
        logger("Loading ECU Config...")

    ecu_info, req_map, resp_map = load_ecu_mapping(ecu_config)

    # ==========================================
    # Parse UDS
    if logger:
        logger("Parsing UDS...")
    
    completed_payloads = reassemble_isotp(messages)


    requests = extract_requests(messages, completed_payloads)

    negative_responses = extract_negative_responses(messages)


    positive_responses = extract_positive_responses(completed_payloads)

    # ==========================================
    # Build Transactions
    #     
    if logger:
        logger("Building Transactions...")
    
    transactions = build_transactions_v4(

        requests,

        positive_responses,

        negative_responses,

        ecu_info,

        timeout=POSITIVE_RESPONSE_TIMEOUT

    )

    # ==========================================
    # Debug
    if logger:
        logger(f"Transactions : {len(transactions)}")

   

    
    

    # ==========================================
    # Report
    if logger:
        logger("Exporting Excel...")

    ecu_reports  = build_ecu_reports(transactions)

    summary = build_summary_report(ecu_reports)

    # export_workbook(summary, ecu_reports, output_file)


    if logger:
        logger("Done.")

    return {

        "summary": summary,

        "ecu_reports": ecu_reports,

        "transactions": transactions

    }
    





