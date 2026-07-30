def load_ecu_mapping(file_excel):
    import pandas as pd

    ecu_df = pd.read_excel(file_excel)

    ecu_info = {}
    req_map = {}
    resp_map = {}

    for _, row in ecu_df.iterrows():

        ecu = str(row["ECU"]).strip()

        req_id = int(str(row["ReqID"]), 16)
        resp_id = int(str(row["RespID"]), 16)

        ecu_info[ecu] = {
            "request": req_id,
            "response": resp_id,
        }

        req_map[req_id] = ecu
        resp_map[resp_id] = ecu

    return ecu_info, req_map, resp_map


def load_vehicle_mapping(vehicle):
    ecu_info = {}
    req_map = {}
    resp_map = {}

    for ecu in vehicle.ecus:

        request_id = _parse_can_id(ecu.request_id)
        response_id = _parse_can_id(ecu.response_id)

        if request_id is None or response_id is None:
            continue

        ecu_info[ecu.name] = {
            "request": request_id,
            "response": response_id,
        }

        req_map[request_id] = ecu.name
        resp_map[response_id] = ecu.name

    return ecu_info, req_map, resp_map


def _parse_can_id(value):
    value = str(value or "").strip()

    if not value:
        return None

    if value.lower().startswith("0x"):
        value = value[2:]

    try:
        return int(value, 16)
    except ValueError:
        return None
