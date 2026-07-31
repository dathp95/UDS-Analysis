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
