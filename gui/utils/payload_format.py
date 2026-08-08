import re


_HEX_ONLY = re.compile(r"^[0-9A-Fa-f\s]*$")


def format_payload_input(value: str) -> str:
    """Format a compact hex payload as uppercase, space-separated bytes.

    Free-form filter text is returned unchanged apart from payload-like hex
    sequences, so terms such as ``VIN`` remain searchable.
    """

    if not value or not _HEX_ONLY.fullmatch(value):
        return value

    compact = re.sub(r"\s+", "", value).upper()
    if not compact:
        return ""

    return " ".join(
        compact[index:index + 2]
        for index in range(0, len(compact), 2)
    )

def _cursor_after_payload_chars(value: str, payload_chars: int) -> int:
    if payload_chars <= 0:
        return 0

    seen = 0
    for index, char in enumerate(value):
        if char.isspace():
            continue

        seen += 1
        if seen == payload_chars:
            return index + 1

    return len(value)


def format_payload_input_with_cursor(value: str, cursor: int) -> tuple[str, int]:
    formatted = format_payload_input(value)
    if formatted == value:
        return formatted, min(cursor, len(formatted))

    payload_chars_before_cursor = sum(
        1
        for char in value[:cursor]
        if not char.isspace()
    )

    return (
        formatted,
        _cursor_after_payload_chars(
            formatted,
            payload_chars_before_cursor,
        ),
    )


def delete_payload_character_at_cursor(
        value: str,
        cursor: int,
    ) -> tuple[str, int]:
    if not _HEX_ONLY.fullmatch(value):
        return value, cursor

    delete_index = None
    for index in range(cursor, len(value)):
        if not value[index].isspace():
            delete_index = index
            break

    if delete_index is None:
        return value, min(cursor, len(value))

    payload_chars_before_cursor = sum(
        1
        for char in value[:cursor]
        if not char.isspace()
    )
    formatted = format_payload_input(
        value[:delete_index] + value[delete_index + 1:]
    )

    return (
        formatted,
        _cursor_after_payload_chars(
            formatted,
            payload_chars_before_cursor,
        ),
    )
