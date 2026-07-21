import bisect

from collections import defaultdict
# from core.asc_reader import *
from core.uds_lookup import (
    MATCH_DID, 
    MATCH_SUB,
    MATCH_ROUTINE,
    POSITIVE_RESPONSE_TIMEOUT,
    SERVICE_NAME_MAP,
    NRC_TABLE,
    get_match_rule,
    get_expected_positive_sid,
    get_negative_response_info,
    get_service_info,
    get_identifier_info,
    get_routine_info,
    get_display_name,
    get_sub_function_info
    )



# TODO: Structure python build_transactions.py


# ├── get_payload_sid()
# ├── get_expected_positive_sid()

# ├── parse_negative_response()
# ├── get_nrc_name()

# ├── find_matching_positive_response()
# ├── find_matching_negative_response()

# └── build_transactions()

# build_transactions.py

# get_match_key()

# find_matching_positive_response()

# find_negative_responses_between()

# build_positive_response_index()

# build_negative_response_index()

# get_transaction_ecu()

# create_transaction()

# build_transactions_v4()

# print_transaction()


#============================

def get_match_key(payload):

    bytes_list = payload.split()

    if not bytes_list:
        return None

    sid = int(
        bytes_list[0],
        16
    )

    rule = get_match_rule(sid)

    # ==================================
    # DID-based Services
    # 22 F1 90 ↔ 62 F1 90
    # 2E F1 90 ↔ 6E F1 90

    if rule == MATCH_DID:
        if len(bytes_list) < 3:
            return None
        
        return " ".join(bytes_list[1:3])
    
    # ==========================
    # SubFunction

    if rule == MATCH_SUB:

        if len(bytes_list) < 2:
            return None

        return bytes_list[1]
    
    # ==========================
    # Routine

    if rule == MATCH_ROUTINE:

        if len(bytes_list) < 4:
            return None

        return " ".join(
            bytes_list[2:4]
        )

    # ==========================
    # No Match

    return None

"""
    find_matching_positive_response() sẽ chỉ còn 4 bước:

        1. Lấy expected SID

        2. Lấy match key

        3. Binary Search

        4. So sánh

Toàn bộ phần:

        Positive SID
        Match Rule
        DID
        Routine
        SubFunction

đều đã được ẩn phía sau uds_lookup.py.
"""


def find_matching_positive_response(
    request,
    positive_responses,
    response_can_id,
    timeout=POSITIVE_RESPONSE_TIMEOUT
):

    request_time = request["timestamp"]

    request_payload = request["payload"]

    if not request_payload:
        return None

    # =========================
    # Expected SID

    request_sid = int(

        request_payload.split()[0],

        16

    )

    expected_sid = get_expected_positive_sid(
        request_sid
    )

    if expected_sid is None:
        return None

    # =========================
    # Match Key

    request_key = get_match_key(
        request_payload
    )

    # =========================
    # Binary Search

    timestamps = [

        response["timestamp"]

        for response in positive_responses

    ]

    start = bisect.bisect_left(

        timestamps,

        request_time

    )

    # =========================
    # Search

    for response in positive_responses[start:]:

        if (

            response["timestamp"]

            - request_time

        ) > timeout:

            break

        response_payload = response["payload"]

        if not response_payload:
            continue

        # SID

        if int(

            response_payload.split()[0],

            16

        ) != expected_sid:

            continue

        # Match Key

        response_key = get_match_key(
            response_payload
        )

        if (

            request_key is not None

            and

            response_key is not None

            and

            request_key != response_key

        ):

            continue

        return response

    return None
  


# TODO: OK => Matching ECU - Request CAN ID - Response CAN ID - Positive SID - DID (22 F1 xx)
# TODO: NOK => NRC - Timestamp Window - Multi Request Queue

def get_transaction_ecu(request_can_id, ecu_info):

    for ecu_name, info in ecu_info.items():

        if info["request"] == request_can_id:

            return {

                "name": ecu_name,

                "request_can_id": info["request"],

                "response_can_id": info["response"]

            }

    return None

def calculate_response_time(request, positive):

    if positive is None:
        return None

    return (

        positive["timestamp"] - request["timestamp"]

    )

def determine_status(positive, negative_list):

    if positive is not None:

        return "OK"

    if len(negative_list) > 0:

        return "NRC_ONLY"

    return "TIMEOUT"

def count_nrc_response_pending(negative_responses):

    """
    Count NRC 0x78 (Response Pending)

    Input:
        [
            {"payload":"7F 22 78"},
            {"payload":"7F 22 78"},
            {"payload":"7F 22 31"}
        ]

    Output:
        2
    """

    count_response_pending = 0
    

    for response in negative_responses:

        info = get_negative_response_info(response["payload"])

        if info["nrc"] == "78":

            count_response_pending += 1

    return count_response_pending

def get_final_response_payload(transaction):
    """
    Return the final response payload for one transaction.

    Priority
    --------
    1. Positive Response
    2. Last Negative Response
    3. Empty string
    """

    # -------------------------
    # Positive Response

    positive = transaction.get(

        "positive_response"

    ) 

    if positive:

        return positive["payload"]

    # -------------------------
    # Last Negative Response

    negative_list = transaction.get(

        "negative_responses",

        []

    )

    if negative_list:

        return negative_list[-1]["payload"]

    # -------------------------
    # No Response

    return ""

def create_transaction(ecu, request, positive, negative_list):
     
    # request {'timestamp': 751.688745, 'can_id': 1665, 'payload': '22 F1 23'}
    response_time = calculate_response_time(request, positive)

    status = determine_status(positive, negative_list)

    service = get_service_info(request["payload"])

    identifier = get_identifier_info(request["payload"])

    routine = get_routine_info(request["payload"])

    display_name = get_display_name(request["payload"])

    sub_function = get_sub_function_info(request["payload"])

    response_pending_count = count_nrc_response_pending(negative_list)

       
    return {

        "ecu": ecu["name"],

        "service_id": service["id"],

        "service_name": service["name"],

        "display_name": display_name,

        "identifier": identifier.get("id"),

        "identifier_name": identifier.get("name"),


        "sub_function": sub_function["id"],


        "routine_id": routine["id"],

        "routine_name": routine["name"],


        "request": request,

        "negative_responses": negative_list,

        "positive_response": positive,

        "response_pending_count": response_pending_count,


        "response_time": response_time,

        "status": status

    }




def get_payload_sid(payload):

    first_byte = payload.split()[0]

    return int(
        first_byte,
        16
    )

# TODO: Read NRC: ECU đã nhận request -> Nhưng chưa xử lý xong -> Hãy chờ thêm
# 7F = Negative Response
# 22 = Request SID
# 78 = Response Pending

# INPUT: HEX: 7F XX XX -> OUTPUT: DEC (INT) XX XX
def parse_negative_response(payload):
    bytes_list = payload.split()

    if len(bytes_list) < 3:
        return None

    if bytes_list[0] != "7F":
        return None
    

    return {

        "request_sid":
            int(bytes_list[1], 16),

        "nrc":
            int(bytes_list[2], 16)
    }

# INPUT: Code NRC XX (HEX: 78, OR DEC) => NAME of NRC

def get_nrc_name(nrc):
    

    return NRC_TABLE.get(
        nrc,
        "Unknown NRC"
    )




# TODO: Request -> Tìm NRC gần nhất 


def find_matching_negative_response(
    request,
    negative_responses,
    response_can_id
):

    request_time = request["timestamp"]

    request_payload = request["payload"]

    request_sid = get_payload_sid(
        request_payload
    )

    # ======================================
    # Tìm NRC phù hợp

    for negative_response in negative_responses:

        # CAN ID phải đúng ECU

        if negative_response["can_id"] != response_can_id:
            continue

        # NRC phải xảy ra sau Request

        if negative_response["timestamp"] < request_time:
            continue

        info = parse_negative_response(
            negative_response["payload"]
        )

        if info is None:
            continue

        # SID phải khớp

        if info["request_sid"] != request_sid:
            continue

        return negative_response

    return None

def find_negative_responses_between(

    request_time,

    positive_time,

    negative_responses,

    response_can_id

):

    results = []

    for nrc in negative_responses:

        # Response trước Request
        if nrc["timestamp"] < request_time:
            continue

        # Đã vượt Positive Response
        if nrc["timestamp"] > positive_time:
            break

        results.append(nrc)

    return results


# TODO: positive_responses
# Input
    # 1 request
    # Danh sách positive_responses
    # response_can_id của ECU tương ứng

# Output

    # Positive Response đầu tiên thỏa mãn:
    # cùng CAN ID response
    # timestamp lớn hơn request
    # SID phản hồi đúng với SID request (22 -> 62, 27 -> 67, ...)) 

# Create helper

def get_identifier(payload):

    bytes_list = payload.split()

    if len(bytes_list) < 3:
        return None

    return " ".join(
        bytes_list[1:3]
    )

def get_response_identifier(payload):

    bytes_list = payload.split()

    if len(bytes_list) < 2:
        return None

    sid = int(
        bytes_list[0],
        16
    )

    # ==========================
    # ReadDataByIdentifier
    # 22 F1 90
    # 62 F1 90 ...

    if sid in [0x22, 0x62]:

        if len(bytes_list) < 3:
            return None

        return " ".join(
            bytes_list[1:3]
        )

    # ==========================
    # WriteDataByIdentifier
    # 2E F1 90 ...
    # 6E F1 90

    if sid in [0x2E, 0x6E]:

        if len(bytes_list) < 3:
            return None

        return " ".join(
            bytes_list[1:3]
        )

    # ==========================
    # SecurityAccess
    # 27 01
    # 67 01

    if sid in [0x27, 0x67]:

        return bytes_list[1]

    # ==========================
    # DiagnosticSessionControl
    # 10 03
    # 50 03

    if sid in [0x10, 0x50]:

        return bytes_list[1]

    # ==========================
    # ECUReset
    # 11 01
    # 51 01

    if sid in [0x11, 0x51]:

        return bytes_list[1]

    # ==========================
    # CommunicationControl
    # 28 03
    # 68 03

    if sid in [0x28, 0x68]:

        return bytes_list[1]

    # ==========================
    # RoutineControl
    # 31 01 F0 01
    # 71 01 F0 01

    if sid in [0x31, 0x71]:

        if len(bytes_list) < 4:
            return None

        return " ".join(
            bytes_list[1:4]
        )

    # ==========================
    # Không cần identifier

    return None



def build_timestamp_list(responses):

    return [

        response["timestamp"]

        for response in responses

    ]

def get_start_index(responses, request_time):

    timestamps = build_timestamp_list(
        responses
    )

    return bisect.bisect_left(

        timestamps,

        request_time

    )



def is_matching_response(
    request_payload,
    response_payload
):

    request_bytes = request_payload.split()

    response_bytes = response_payload.split()

    # Không đủ dữ liệu
    if len(request_bytes) < 3:
        return True

    if len(response_bytes) < 3:
        return False

    # So sánh DID

    if request_bytes[1] != response_bytes[1]:
        return False

    if request_bytes[2] != response_bytes[2]:
        return False

    return True



def build_positive_response_index(
    positive_responses
):

    index = {}

    for response in positive_responses:

        can_id = response["can_id"]

        if can_id not in index:

            index[can_id] = []

        index[can_id].append(response)

    return index

def build_negative_response_index(
    negative_responses
):

    index = {}

    for response in negative_responses:

        can_id = response["can_id"]

        if can_id not in index:

            index[can_id] = []

        index[can_id].append(response)

    return index


def build_transactions_v4(

    requests,

    positive_responses,

    negative_responses,

    ecu_info,

    timeout

):

    transactions = []

    positive_index = build_positive_response_index(positive_responses)

    negative_index = build_negative_response_index(negative_responses)

    for request in requests:

        # =========================
        # ECU Mapping

        ecu = get_transaction_ecu(

                request["can_id"],

                ecu_info

            )        

        if ecu is None:
            continue

        response_can_id = ecu["response_can_id"]

        # =========================
        # Positive Response

        responses = positive_index.get(response_can_id,[])
               
               
        positive_response = (

            find_matching_positive_response(

                request,

                responses,

                response_can_id,

                timeout

            )

        )

        # =========================
        # Negative Responses

        responses = negative_index.get(
            response_can_id,
            []
        )

        end_time = (
            positive_response["timestamp"]
            if positive_response
            else request["timestamp"] + timeout
        )

        negative_list = find_negative_responses_between(
            request["timestamp"],
            end_time,
            responses,
            response_can_id
        )

        # =========================
        # Create Transaction

        transaction = (

            create_transaction(

                ecu,

                request,

                positive_response,

                negative_list

            )

        )

        transactions.append(

            transaction

        )

    return transactions




def print_transaction(tx):

    print("-" * 80)

    # ======================================
    # ECU & Status

    print(
        f"ECU: {tx['ecu']}"
    )

    print(
        f"STATUS: {tx['status']}"
    )

    # ======================================
    # Request

    request = tx["request"]

    print(
        f"REQ TIME: {request['timestamp']:.6f}"
    )

    print(
        f"REQ CAN : {hex(request['can_id'])}"
    )

    print(
        f"REQ: {request['payload']}"
    )

    # ======================================
    # Negative Responses

    negative_responses = tx[
        "negative_responses"
    ]

    print(
        f"NRC Count: {len(negative_responses)}"
    )

    for nrc in negative_responses:

        print(
            f"  [{nrc['timestamp']:.6f}] {nrc['payload']}"
        )

    # ======================================
    # Positive Response

    positive = tx[
        "positive_response"
    ]

    if positive is not None:

        print(
            f"POS TIME: {positive['timestamp']:.6f}"
        )

        print(
            f"POS CAN : {hex(positive['can_id'])}"
        )

        print(
            f"Response Time: {tx['response_time']:.3f}s"
        )

        print(
            f"POS: {positive['payload']}"
        )

    else:

        print(
            "POS: None"
        )

def get_service_name(payload):

    if not payload:
        return "Unknown"

    sid = int(
        payload.split()[0],
        16
    )

    return SERVICE_NAME_MAP.get(
        sid,
        f"Unknown_{hex(sid)}"
    )

def debug_request(
        request_payload,
        transactions
    ):

        for tx in transactions:

            if tx["request"]["payload"] == request_payload:

                print_transaction(tx)