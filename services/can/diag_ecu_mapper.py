from services.can.ecu_diagnostic_resolver import parse_can_id


def find_ecu_by_can_ids(vehicle, request_id, response_id):
    """
    Find exactly one V-CODE ECU matching the original
    CAN Request/Response ID pair.

    Return the V-CODE ECU name, or "" if unresolved.
    """
    if vehicle is None:
        return ""

    for value in (request_id, response_id):
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 0x7FF
        ):
            return ""

    matches = []

    for ecu in vehicle.ecus:
        try:
            tx_id = parse_can_id(ecu.request_id)
            rx_id = parse_can_id(ecu.response_id)
        except (ValueError, TypeError):
            continue

        if tx_id == request_id and rx_id == response_id:
            matches.append(ecu.name)

    # Never guess when addressing is duplicated.
    if len(matches) != 1:
        return ""

    return matches[0]