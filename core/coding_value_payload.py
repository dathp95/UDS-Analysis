from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class PayloadWriteResult:
    payload: list[int]
    changed_indexes: list[int]
    success: bool


def parse_payload_text(payload: str) -> list[int]:
    return [
        int(token, 16)
        for token in re.findall(r"[0-9A-Fa-f]{2}", payload or "")
    ]


def format_payload_bytes(payload_bytes: list[int]) -> str:
    return " ".join(
        f"{value:02X}"
        for value in payload_bytes
    )


def extract_raw_value(
        payload_bytes: list[int],
        byte_pos: int | None,
        bit_pos: Any,
        bit_length: Any,
    ) -> str:
    bit_offset = to_int(bit_pos)
    bit_count = to_int(bit_length)
    if (
            bit_offset is None
            or bit_count is None
            or bit_count <= 0
            or byte_pos is None
            or byte_pos < 0
            or byte_pos >= len(payload_bytes)
        ):
        return ""

    if bit_offset == 0 and bit_count % 8 == 0:
        byte_count = bit_count // 8
        selected = payload_bytes[byte_pos:byte_pos + byte_count]
        if len(selected) != byte_count:
            return ""
        return format_payload_bytes(selected)

    byte_count = (bit_offset + bit_count + 7) // 8
    selected = payload_bytes[byte_pos:byte_pos + byte_count]
    if len(selected) != byte_count:
        return ""

    container = int.from_bytes(
        bytes(selected),
        byteorder="little",
    )
    raw_int = (container >> bit_offset) & ((1 << bit_count) - 1)
    return format_raw_int(
        raw_int,
        bit_count,
        max(1, (bit_count + 3) // 4),
    )


def write_raw_value(
        payload_bytes: list[int],
        byte_pos: int | None,
        bit_pos: Any,
        bit_length: Any,
        raw_value: str,
    ) -> PayloadWriteResult:
    updated = list(payload_bytes)
    bit_offset = to_int(bit_pos)
    bit_count = to_int(bit_length)
    if (
            byte_pos is None
            or bit_offset is None
            or bit_count is None
            or byte_pos < 0
            or byte_pos >= len(updated)
        ):
        return PayloadWriteResult(updated, [], False)

    tokens = hex_tokens(raw_value)
    if not tokens:
        return PayloadWriteResult(updated, [], False)

    raw_int = int("".join(tokens), 16)
    if bit_offset == 0 and bit_count % 8 == 0:
        byte_count = bit_count // 8
        if byte_count <= 0 or byte_pos + byte_count > len(updated):
            return PayloadWriteResult(updated, [], False)

        try:
            raw_bytes = raw_int.to_bytes(byte_count, byteorder="big")
        except OverflowError:
            return PayloadWriteResult(updated, [], False)
        for offset, value in enumerate(raw_bytes):
            updated[byte_pos + offset] = value
        changed = list(range(byte_pos, byte_pos + byte_count))
        return PayloadWriteResult(updated, changed, True)

    byte_count = (bit_offset + bit_count + 7) // 8
    if byte_count <= 0 or byte_pos + byte_count > len(updated):
        return PayloadWriteResult(updated, [], False)

    selected = updated[byte_pos:byte_pos + byte_count]
    container = int.from_bytes(bytes(selected), byteorder="little")
    mask = ((1 << bit_count) - 1) << bit_offset
    container = (container & ~mask) | ((raw_int << bit_offset) & mask)
    merged = container.to_bytes(byte_count, byteorder="little")
    for offset, value in enumerate(merged):
        updated[byte_pos + offset] = value
    changed = list(range(byte_pos, byte_pos + byte_count))
    return PayloadWriteResult(updated, changed, True)


def normalize_user_raw_value(raw_value: str, bit_length: Any) -> str | None:
    text = str(raw_value or "").strip()
    if not text:
        return None

    bit_count = to_int(bit_length)
    tokens = hex_tokens(text)
    if not tokens:
        return None

    if is_spaced_hex(text) and bit_count is not None and bit_count <= 4:
        return normalize_raw_tokens(tokens, bit_count)

    hex_text = "".join(tokens)
    raw_int = int(hex_text, 16)
    if bit_count is not None and bit_count > 0:
        max_value = (1 << bit_count) - 1
        if raw_int > max_value:
            return None

    return format_raw_int(raw_int, bit_count, len(hex_text))


def normalize_raw_tokens(tokens: list[str], bit_count: int | None) -> str | None:
    if bit_count is not None and bit_count > 0:
        max_value = (1 << bit_count) - 1
        for token in tokens:
            if int(token, 16) > max_value:
                return None

    formatted = [
        f"{int(token, 16):02X}"
        for token in tokens
    ]
    return " ".join(formatted)


def format_raw_value(raw_value: str, bit_length: Any) -> str:
    text = str(raw_value or "").strip()
    if not text:
        return ""

    bit_count = to_int(bit_length)
    tokens = hex_tokens(text)
    if not tokens:
        return text.removeprefix("0x").removeprefix("0X")

    if is_spaced_hex(text):
        normalized = normalize_raw_tokens(tokens, bit_count)
        return normalized if normalized is not None else " ".join(tokens)

    hex_text = "".join(tokens)
    return format_raw_int(
        int(hex_text, 16),
        bit_count,
        len(hex_text),
    )


def format_raw_int(raw_int: int, bit_count: int | None, source_width: int) -> str:
    if bit_count is not None and bit_count > 0:
        width = max(2, (bit_count + 3) // 4)
    else:
        width = max(2, source_width)

    raw_text = f"{raw_int:0{width}X}"
    if bit_count is not None and bit_count > 4:
        if len(raw_text) % 2:
            raw_text = "0" + raw_text
        return " ".join(
            raw_text[index:index + 2]
            for index in range(0, len(raw_text), 2)
        )

    return raw_text


def hex_tokens(raw_value: str) -> list[str]:
    text = str(raw_value or "").strip()
    text = re.sub(r"(?i)0x", "", text)
    tokens = re.findall(r"[0-9A-Fa-f]+", text)
    if not tokens or "".join(tokens) != re.sub(r"\s+", "", text):
        return []

    return tokens


def is_spaced_hex(raw_value: str) -> bool:
    return bool(re.search(r"\s", str(raw_value or "").strip()))


def to_int(value: Any) -> int | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        return int(text, 0)
    except ValueError:
        pass

    match = re.match(r"^(\d+)(?:\.0+)?(?:\D.*)?$", text)
    if match:
        return int(match.group(1), 10)

    return None
