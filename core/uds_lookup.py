from core.config_loader import *


UDS_CONFIG = load_uds_config()
UDS_DISPLAY_NAMES = load_display_names()

POSITIVE_RESPONSE_TIMEOUT = float(

    UDS_CONFIG["timeout"]["positive_response"]

)

REQUEST_SERVICE_LIST = {

    int(service, 16)

    for service in UDS_CONFIG["services"]

}

SERVICE_NAME_MAP = UDS_CONFIG["services"]
POSITIVE_SID_MAP = UDS_CONFIG["positive_sid"]
DID_NAME_MAP = UDS_CONFIG["dids"]
NRC_NAME_MAP = UDS_CONFIG["nrc"]
ROUTINE_NAME_MAP = UDS_CONFIG.get("routine_ids",{})
MATCH_RULE_MAP = UDS_CONFIG["match_rule"]
DISPLAY_NAME_MAP = {
        key: value.get("display_name", key)
        for key, value in UDS_DISPLAY_NAMES.items()
    }

MATCH_DID = "did"
MATCH_SUB = "sub"
MATCH_ROUTINE = "routine"
MATCH_NONE = "none"

POSITIVE_SERVICE_LIST = {

    0x50,
    0x51,
    0x54,
    0x59,
    0x62,
    0x67,
    0x68,
    0x6E,
    0x71,
    0xC5

}

NRC_TABLE = {

    0x10: "General Reject",

    0x11: "Service Not Supported",

    0x12: "SubFunction Not Supported",

    0x13: "Incorrect Message Length",

    0x22: "Conditions Not Correct",

    0x31: "Request Out Of Range",

    0x33: "Security Access Denied",

    0x35: "Invalid Key",

    0x36: "Exceeded Number Of Attempts",

    0x37: "Required Time Delay Not Expired",

    0x78: "Response Pending"
    }
# ==========================================
# Service
# ==========================================

def get_service_name(service_id):

    """
    Input:
        0x22

    Output:
        ReadDataByIdentifier
    """

    key = f"{service_id:02X}"

    return SERVICE_NAME_MAP.get(

        key,

        f"Unknown Service ({key})"

    )

# ==========================================
# Positive SID
# ==========================================

def get_expected_positive_sid(service_id):

    """
    Input:
        0x22

    Output:
        0x62
    """

    key = f"{service_id:02X}"

    sid = POSITIVE_SID_MAP.get(key)

    if sid is None:
        return None

    return int(
        sid,
        16
    )  

# ==========================================
# DID
# ==========================================

def get_did_name(did):

    """
    Input:
        0xF190
        "F190"

    Output:
        VIN
    """

    if isinstance(did, int):

        did = f"{did:04X}"

    else:

        did = did.upper()

    return DID_NAME_MAP.get(

        did,

        "UNKNOWN"

    )

# ==========================================
# NRC
# ==========================================

def get_nrc_name(nrc):

    """
    Input:
        0x78
        120

    Output:
        Response Pending
    """

    key = f"{nrc:02X}"

    return NRC_NAME_MAP.get(

        key,

        "Unknown NRC"

    )

# ==========================================
# Routine
# ==========================================

def get_routine_name(routine_id):

    """
    Input:
        0x020E
        "020E"

    Output:
        Check Programming Preconditions
    """

    if isinstance(routine_id, int):

        routine_id = f"{routine_id:04X}"

    else:

        routine_id = routine_id.upper()

    return ROUTINE_NAME_MAP.get(

        routine_id,

        "UNKNOWN"

    )

def get_match_rule(service_id):

    key = f"{service_id:02X}"

    return MATCH_RULE_MAP.get(key,MATCH_NONE)

# TODO: service_id -> service_name
"""
    Input:
        22 F1 90

    Output:
        {
            "id": "22",
            "name": "ReadDataByIdentifier"
        }
"""

def get_service_info(payload):  

    if not payload:
        return None

    sid = payload.split()[0].upper()

    return {

        "id": sid,

        "name": get_service_name(
            int(sid, 16)
        )

    }

# TODO: F190 -> VIN
"""
    Input:
        22 F1 90

    Output:
        {
            "id": "F190",
            "name": "VIN"
        }

    Nếu service không dùng DID:
        None
    """
def get_identifier_info(payload):   

    empty = {

        "id": None,
        "name": None

    }
    
    if not payload:
        return empty

    bytes_list = payload.split()

    if len(bytes_list) < 3:
        return empty

    sid = int(bytes_list[0], 16)

    rule = get_match_rule(sid)

    if rule != MATCH_DID:

        return empty

    did = "".join(bytes_list[1:3]).upper()

    return {

        "id": did,

        "name": get_did_name(did)

    }


# TODO: 31 01 | 02 0E| 01 => Routine Information
    """
        Input:
            31 01 02 0E 01

        Output:
            {
                "id": "020E",
                "name": "Check Programming Preconditions"
            }

        Nếu service không dùng Routine:
            {
                "id": None,
                "name": None
            }
    """


def get_routine_info(payload):

    empty = {

        "id": None,

        "name": None

    }

    if not payload:
        return empty

    bytes_list = payload.split()

    # RoutineControl:
    # SID SubFunction RID_H RID_L ...

    if len(bytes_list) < 4:
        return empty

    sid = int(bytes_list[0], 16)

    rule = get_match_rule(sid)

    if rule != MATCH_ROUTINE:
        return empty

    routine_id = "".join(

        bytes_list[2:4]

    ).upper()

    return {

        "id": routine_id,

        "name": get_routine_name(routine_id)

    }

def get_display_name(payload):

    if not payload:
        return "UNKNOWN"

    bytes_list = payload.split()

    # Thử match từ dài đến ngắn
    for length in (4, 3, 2, 1):

        if len(bytes_list) >= length:

            key = " ".join(bytes_list[:length])

            if key in DISPLAY_NAME_MAP:

                return DISPLAY_NAME_MAP[key]

    return "UNKNOWN"

# TODO: Subfunction 10 03 -> 03
"""
        Input:
            10 03
            27 01
            28 01
            31 01 02 0E

        Output:
            {
                "id": "03"
            }

        Nếu service không có SubFunction:
            {
                "id": None
            }
"""
def get_sub_function_info(payload):    

    empty = {

        "id": None

    }

    if not payload:
        return empty

    bytes_list = payload.split()

    if len(bytes_list) < 2:
        return empty

    sid = int(

        bytes_list[0],

        16

    )

    rule = get_match_rule(sid)

    if rule != MATCH_SUB and rule != MATCH_ROUTINE:

        return empty

    return {

        "id": bytes_list[1].upper()

    }


# TODO: Support COUNT NEGATIVE info
"""
    Input:
        7F 22 78

    Output:
        {
            "service_id": "22",
            "service_name": "ReadDataByIdentifier",
            "nrc": "78",
            "nrc_name": "Response Pending"
        }

    Nếu payload không hợp lệ:
        {
            "service_id": None,
            "service_name": None,
            "nrc": None,
            "nrc_name": None
        }
"""

def get_negative_response_info(payload):

    empty = {

        "service_id": None,

        "service_name": None,

        "nrc": None,

        "nrc_name": None

    }

    if not payload:
        return empty

    bytes_list = payload.split()

    if len(bytes_list) < 3:
        return empty

    # Chỉ xử lý Negative Response
    if bytes_list[0].upper() != "7F":
        return empty

    try:

        service_id = bytes_list[1].upper()

        nrc = bytes_list[2].upper()

        return {

            "service_id": service_id,

            "service_name": get_service_name(

                int(service_id, 16)

            ),

            "nrc": nrc,

            "nrc_name": get_nrc_name(

                int(nrc, 16)

            )

        }

    except ValueError:

        return empty

def is_request_service(service_id):

    return service_id in REQUEST_SERVICE_LIST

def get_service_id(payload):

    """
    Input:
        "22 F1 90"

    Output:
        0x22
    """

    if not payload:
        return None

    return int(

        payload.split()[0],

        16

    )

def is_positive_service(service_id):

    return service_id in POSITIVE_SERVICE_LIST