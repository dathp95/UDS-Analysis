# ========STRUCTURE============
# parse_asc_line()

# load_asc()

# reassemble_isotp()

# extract_single_frame_requests()

# extract_negative_responses()

# extract_positive_responses()
from pathlib import Path
from core.convert_blf import blf_to_asc, get_blf_channels


from core.uds_lookup import (
                is_request_service, 
                get_service_id,
                is_positive_service
            )

def parse_asc_line(line):

    # Split by whitespace
    parts = line.split()   

        # Not enough columns means this is not a valid CAN frame.
    if len(parts) < 13:
        return None

    try:

        timestamp = float(parts[0])

        channel = int(parts[1])

        # Convert HEX string to int.
        can_id = int(parts[2], 16)

        dlc = int(parts[5])
        # Data format: DEC NOT HEX
        data = []

        for byte_str in parts[6:6 + dlc]:
            data.append(
                int(byte_str, 16)
            )

        return {
            "timestamp": timestamp,
            "channel": channel,
            "can_id": can_id,
            "dlc": dlc,
            "data": data
        }
          

    except:
        # Parse error.
        return None
    
# TODO: INPUT: file ASC -> OUT: messages

def load_asc(file_name, channel=None):

    messages = []
    selected_channel_found = channel is None

    with open(
        file_name,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as f:

        for line in f:

            msg = parse_asc_line(line)

            if msg is None:
                continue

            if channel is not None and msg["channel"] != channel:
                continue

            selected_channel_found = True
            messages.append(msg)

    if not selected_channel_found:
        raise ValueError(
            "Selected Diagnostic Channel was not found in the log."
        )

    return messages


def _get_asc_channels(file_name):

    channels = set()

    with open(
        file_name,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as f:

        for line in f:

            msg = parse_asc_line(line)

            if msg is not None:
                channels.add(msg["channel"])

    return sorted(channels)


def get_log_channels(log_file):

    suffix = Path(log_file).suffix.lower()

    if suffix == ".asc":
        return _get_asc_channels(log_file)

    if suffix == ".blf":
        return get_blf_channels(log_file)

    raise ValueError(f"Unsupported log format: {suffix}")


def _fn_blf_channel_to_asc_channel(channel):

    if channel is None:
        return None

    # python-can ASCWriter serializes zero-based bus channels as one-based ASC channels.
    return int(channel) + 1


def load_log(log_file, channel=None):

    suffix = Path(log_file).suffix.lower()

    if suffix == ".asc":
        return load_asc(log_file, channel=channel)

    if suffix == ".blf":
        asc_file = blf_to_asc(log_file)
        return load_asc(
            asc_file,
            channel=_fn_blf_channel_to_asc_channel(channel),
        )

    raise ValueError(f"Unsupported log format: {suffix}")

# TODO: INPUT: messages -> OUT: CANID + payload
def reassemble_isotp(messages):

    sessions = {}

    completed_payloads = []

    # Iterate messages.

    for msg in messages:


        can_id = msg["can_id"]

        data = msg["data"]

        frame_type = data[0] >> 4
        if frame_type == 0:

            payload_len = data[0] & 0x0F

            completed_payloads.append({
                "timestamp": msg["timestamp"],
                "can_id": can_id,
                "payload": bytes(
                    data[1:1 + payload_len]).hex(" ").upper()                
            })

        # Step 1: First Frame: 10 14 62 F1 90 52 4C 4E

        elif frame_type == 1:

            pci = data[0]

            expected_length = (
                (pci & 0x0F) << 8
            ) | data[1]

            sessions[can_id] = {
                "timestamp": msg["timestamp"],

                "payload": bytearray(
                    data[2:]
                ),

                "expected_length": expected_length
            }
        # Step 2: Consecutive Frame
        
        elif frame_type == 2:

            if can_id not in sessions:
                continue

            session = sessions[can_id]

            session["payload"] += bytes(
                data[1:]
            )
        # Step 3: Check wether data enough

            current_payload = session["payload"]

            expected_length = session[
                "expected_length"
            ]

            if len(current_payload) >= expected_length:
                final_payload = bytes(
                    current_payload
                )[:expected_length]

                    # Step 4: SAVE completed_payloads
        
                completed_payloads.append({
                    "timestamp": session["timestamp"],

                    "can_id": can_id,

                    "payload": final_payload.hex(" ").upper()
                    })

                # Step 5: Delete session:

                del sessions[can_id]

    

    # count = 0

    # for message in completed_payloads:

    #     payload = message["payload"]

    #     if isinstance(payload, bytes):
    #         payload = payload.hex(" ").upper()

    #     if payload.startswith("2E"):

    #         count += 1

    

    return completed_payloads



# TODO: Find Frame REQUEST to seperate:  03 22 F1 90 - 02 27 03 -02 10 03...
# TODO: Skip TESTER PRESENT: 3E 80 - Check Service ID, KEEP 7F XX XX
def extract_single_frame_requests(messages):
    requests = []

    for msg in messages:

        can_id = msg["can_id"]

        data = msg["data"]

        # ==================================
        # Single Frame only

        frame_type = data[0] >> 4

        if frame_type != 0:
            continue

        # ==================================
        # Get payload

        payload_length = data[0]

        payload = data[
            1 : 1 + payload_length
        ]

        # No data

        if len(payload) == 0:
            continue

        # ==================================
        # Service ID

        service_id = payload[0]

        # Skip Tester Present
        # 3E 80

        if service_id == 0x3E:
            continue

        if not is_request_service(service_id):
            continue

        # ==================================
        # Save

        requests.append({
            "timestamp": msg["timestamp"],

            "can_id": can_id,

            "payload": bytes(
                payload
            ).hex(" ").upper()

        })

    return requests

def extract_requests(
        messages,
        completed_payloads        

    ):    
    requests = []     

    for message in completed_payloads:

        payload = message["payload"]

        sid = get_service_id(payload)

        

        if sid is None:
            continue

        if not is_request_service(sid):
            continue

        requests.append(

            message

        )

    return sorted(

        requests,

        key=lambda x: x["timestamp"]

    ) 




# TODO: CHECK negative responses
def extract_negative_responses(messages):

    negative_responses = []

    for msg in messages:

        can_id = msg["can_id"]

        data = msg["data"]

        # ==============================
        # Single Frame only

        frame_type = data[0] >> 4

        if frame_type != 0:
            continue

        # ==============================
        # Get payload

        payload_length = data[0]

        payload = data[
            1 : 1 + payload_length
        ]

        # No data

        if len(payload) == 0:
            continue

        # ==============================
        # Negative Response

        # Format:
        # 03 7F 22 78
        #    ^^
        #    7F = Negative Response

        if payload[0] != 0x7F:
            continue

        # ==============================
        # Save

        negative_responses.append({
            "timestamp": msg["timestamp"],

            "can_id": can_id,

            "payload": bytes(
                payload
            ).hex(" ").upper()

        })

    return negative_responses



# TODO: Extract positive responses INPUT: completed_payloads NOT Messages
def extract_positive_responses(completed_payloads):
    
    positive_responses = []

    # Positive Response SID
    

    for item in completed_payloads:

        can_id = item["can_id"]

        payload = item["payload"]

        # No data
        if len(payload) == 0:
            continue

        service_id = get_service_id(payload)

        if service_id is None:
            continue

        if not is_positive_service(service_id):
            continue

        positive_responses.append({
            "timestamp":item["timestamp"],

            "can_id": can_id,

            "payload": payload

        })

    return positive_responses

# TODO - SHOW: Convert bytes -> HEX 
def show_positive_responses(positive_responses):

    

    for item in positive_responses:

        can_id = item["can_id"]

        payload = item["payload"]

        # Convert bytes payload
        if isinstance(payload, bytes):

            payload = payload.hex(
                " "
            ).upper()

      

def show_requests(requests):

    print(
        "Requests:",
        len(requests)
    )

    print()

    for item in requests[:10]:

        print(
            hex(item["can_id"]),
            item["payload"]
        )

def show_positive_responses(
    positive_responses
):

    print(
        "Positive Responses:",
        len(positive_responses)
    )

    print()

    for item in positive_responses[:10]:

        print(
            hex(item["can_id"]),
            item["payload"]
        )
