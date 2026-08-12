import re


_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]*$")


def parse_hex_bytes(value):
    normalized = re.sub(r"\s+", "", value or "")
    if len(normalized) % 2 != 0:
        raise ValueError("Invalid HEX input: byte data must have even length.")
    if not _HEX_PATTERN.fullmatch(normalized):
        raise ValueError("Invalid HEX input: only 0-9 and A-F are allowed.")

    return bytes.fromhex(normalized)


def calculate_crc8_sae_j1850(data):
    crc = 0xFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x1D) & 0xFF
            else:
                crc = (crc << 1) & 0xFF

    return crc ^ 0xFF
