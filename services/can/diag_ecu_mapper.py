from services.can.ecu_diagnostic_resolver import parse_can_id


def find_ecu_by_can_ids(vehicle, request_id, response_id):
    matches = []

    for ecu in vehicle.ecus:
        try:
            tx = parse_can_id(ecu.request_id)
            rx = parse_can_id(ecu.response_id)
        except ValueError:
            continue

        if tx == request_id and rx == response_id:
            matches.append(ecu.name)

    if len(matches) == 1:
        return matches[0]

    return ""