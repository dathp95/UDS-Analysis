import re


SUPPORTED_FORMATS = (
    "Hexadecimal",
    "Decimal",
    "ASCII",
    "Binary",
    "TXT",
    "Octa",
)


def convert_data(value: str, from_format: str, to_format: str) -> str:
    if from_format == to_format:
        raise ValueError("From and To formats must not be the same.")
    if from_format not in SUPPORTED_FORMATS or to_format not in SUPPORTED_FORMATS:
        raise ValueError("Unsupported conversion format.")

    data = _parse_value(value, from_format)
    return _format_value(data, to_format)


def _parse_value(value: str, data_format: str) -> bytes:
    if data_format == "Hexadecimal":
        return _parse_hex(value)
    if data_format == "Decimal":
        return _parse_decimal(value)
    if data_format == "ASCII":
        return _parse_ascii(value)
    if data_format == "Binary":
        return _parse_binary(value)
    if data_format == "TXT":
        return _parse_txt(value)
    if data_format == "Octa":
        return _parse_octa(value)

    raise ValueError("Unsupported conversion format.")


def _format_value(data: bytes, data_format: str) -> str:
    if data_format == "Hexadecimal":
        return " ".join(f"{byte:02X}" for byte in data)
    if data_format == "Decimal":
        return " ".join(str(byte) for byte in data)
    if data_format == "ASCII":
        return _format_ascii(data)
    if data_format == "Binary":
        return " ".join(f"{byte:08b}" for byte in data)
    if data_format == "TXT":
        return _format_txt(data)
    if data_format == "Octa":
        return " ".join(f"{byte:o}" for byte in data)

    raise ValueError("Unsupported conversion format.")


def _parse_hex(value: str) -> bytes:
    normalized = re.sub(r"\s+", "", value or "")
    normalized = re.sub(r"(?i)0x", "", normalized)
    if len(normalized) % 2 != 0:
        raise ValueError("Invalid HEX input: byte data must have even length.")
    if not re.fullmatch(r"[0-9a-fA-F]*", normalized):
        raise ValueError("Invalid HEX input: only 0-9 and A-F are allowed.")

    return bytes.fromhex(normalized)


def _parse_decimal(value: str) -> bytes:
    tokens = str(value or "").split()
    if not tokens:
        return b""

    values = []
    for token in tokens:
        if not re.fullmatch(r"\d+", token):
            raise ValueError("Invalid decimal input: use numbers from 0 to 255.")
        byte_value = int(token, 10)
        if byte_value < 0 or byte_value > 255:
            raise ValueError("Invalid decimal input: values must be 0..255.")
        values.append(byte_value)

    return bytes(values)


def _parse_ascii(value: str) -> bytes:
    try:
        return str(value or "").encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError("Invalid ASCII input: only ASCII text is supported.") from error


def _parse_binary(value: str) -> bytes:
    normalized = re.sub(r"\s+", "", value or "")
    if len(normalized) % 8 != 0:
        raise ValueError("Invalid Binary input: byte data must use 8 bits per byte.")
    if not re.fullmatch(r"[01]*", normalized):
        raise ValueError("Invalid Binary input: only 0 and 1 are allowed.")

    return bytes(
        int(normalized[index:index + 8], 2)
        for index in range(0, len(normalized), 8)
    )


def _parse_txt(value: str) -> bytes:
    try:
        return str(value or "").encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError("Invalid TXT input: text cannot be encoded as UTF-8.") from error


def _parse_octa(value: str) -> bytes:
    tokens = str(value or "").split()
    if not tokens:
        return b""

    values = []
    for token in tokens:
        if not re.fullmatch(r"[0-7]+", token):
            raise ValueError("Invalid Octa input: use octal values from 0 to 377.")
        byte_value = int(token, 8)
        if byte_value > 0xFF:
            raise ValueError("Invalid Octa input: values must be 0..377.")
        values.append(byte_value)

    return bytes(values)


def _format_ascii(data: bytes) -> str:
    try:
        return data.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("Invalid ASCII data: bytes are not valid ASCII.") from error


def _format_txt(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("Invalid TXT data: bytes are not valid UTF-8.") from error
