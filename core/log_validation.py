import re
from pathlib import Path


_PT_BO_INFO_PATTERN = re.compile(
    r"\bPT\s+BO\s+INFO\b",
    re.IGNORECASE,
)
_SCAN_CHUNK_SIZE = 64 * 1024
_PATTERN_TAIL_SIZE = 64


def has_multiple_pt_bo_info_markers(file_path: str | Path) -> bool:
    """Return whether a log contains more than one PT BO INFO marker."""

    with open(
        file_path,
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as log_file:
        marker_count = 0
        tail = ""

        while chunk := log_file.read(_SCAN_CHUNK_SIZE):
            content = tail + chunk
            new_content_start = len(tail)

            for match in _PT_BO_INFO_PATTERN.finditer(content):
                if match.end() <= new_content_start:
                    continue

                marker_count += 1

                if marker_count > 1:
                    return True

            tail = content[-_PATTERN_TAIL_SIZE:]

    return False
