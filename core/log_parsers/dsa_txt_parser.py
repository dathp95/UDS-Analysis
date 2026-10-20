import logging
import re
from collections.abc import Iterator
from pathlib import Path

from core.log_parsers.base import BaseTextLogParser, read_text_header


_LOGGER = logging.getLogger(__name__)
_SIGNATURE = re.compile(r"^[ \t]*#!DSAVci\.log[ \t\r]*$", re.MULTILINE)
_FORMAT = re.compile(r"^[ \t]*\$Log\.Format\.String[ \t]*=[ \t]*DSA-TEXT[ \t\r]*$", re.MULTILINE)
_CHANNEL_COUNT = re.compile(r"\$Log\.Channels\s*=\s*([0-9]+)\s*$")
_CHANNEL_BUS = re.compile(r"\$Log\.Ch([0-9]+)\.BusType\s*=\s*CAN(?:_[A-Z0-9]+)?\s*$")
_CAN_MARKER = re.compile(r"\bCh[^\s()]+\s*\(\s*CAN\s*\)", re.IGNORECASE)
_MSG_MARKER = re.compile(r"\bMsg\b", re.IGNORECASE)
_BYTE = re.compile(r"[0-9a-fA-F]{2}")
_FRAME = re.compile(
    r"\s*\[(?P<hours>[0-9]{2}):(?P<minutes>[0-9]{2}):(?P<seconds>[0-9]{2})"
    r"\.(?P<milliseconds>[0-9]{3})\.(?P<microseconds>[0-9]{3})\]\s+"
    r"0x[0-9a-f]+\s+Ch(?P<channel>[0-9]+)\s*\(\s*CAN\s*\)\s+"
    r"F:\s*[0-9a-f]+\s+T:\s*[0-9a-f]+\s+Msg\s+"
    r"(?:T-{15}|-R-{14})\s+E:\s*0x[0-9a-f]+\s+"
    r"(?P<frame_type>\S+)\s+(?P<dlc>[0-9]+)\s+"
    r"id:\s*0x(?P<can_id>[0-9a-f]+)\s*>\s*(?P<data>[^<>]*)<\s*",
    re.IGNORECASE,
)


class DSATextParser(BaseTextLogParser):
    """DSA-TEXT V1: verified classic CAN 11n records, native channel numbering."""

    def can_parse(self, header: str) -> bool:
        header = header.lstrip("\ufeff")
        return bool(_SIGNATURE.search(header) and _FORMAT.search(header))

    def parse_line(self, line: str) -> dict | None:
        """Ignore non-CAN records; raise ValueError for malformed CAN records."""
        if not _CAN_MARKER.search(line):
            return None
        if not _MSG_MARKER.search(line):
            if line.lstrip().startswith("[") and "id:" in line.lower():
                raise ValueError("Malformed CAN record: missing Msg marker")
            return None
        match = _FRAME.fullmatch(line)
        if match is None:
            raise ValueError("Malformed CAN record or timestamp")
        fields = match.groupdict()
        if fields["frame_type"].lower() != "11n":
            raise ValueError(f"Unsupported frame type '{fields['frame_type']}' (V1 supports classic CAN 11n)")
        minutes, seconds = int(fields["minutes"]), int(fields["seconds"])
        if minutes >= 60 or seconds >= 60:
            raise ValueError("Invalid timestamp: minutes and seconds must be 00-59")
        can_id = int(fields["can_id"], 16)
        if can_id > 0x1FFFFFFF:
            raise ValueError("CAN ID exceeds the 29-bit CAN range")
        if can_id > 0x7FF:
            raise ValueError("CAN ID exceeds the 11-bit range for an 11n record")
        dlc = int(fields["dlc"])
        if not 0 <= dlc <= 8:
            raise ValueError("Classic CAN DLC must be 0-8")
        tokens = fields["data"].split()
        if len(tokens) != dlc:
            raise ValueError(f"DLC mismatch: declared {dlc}, found {len(tokens)} bytes")
        if any(_BYTE.fullmatch(token) is None for token in tokens):
            raise ValueError("Invalid hexadecimal CAN data byte")
        total_microseconds = (
            (int(fields["hours"]) * 3600 + minutes * 60 + seconds) * 1_000_000
            + int(fields["milliseconds"]) * 1000 + int(fields["microseconds"])
        )
        return {
            "timestamp": total_microseconds / 1_000_000,
            "channel": int(fields["channel"]),
            "can_id": can_id,
            "dlc": dlc,
            "data": [int(token, 16) for token in tokens],
        }

    def _iter_messages(self, file_path: str | Path) -> Iterator[dict]:
        if not self.can_parse(read_text_header(file_path)):
            raise ValueError("Invalid DSA-TEXT header: both DSA signatures are required.")
        observed = set()
        declared_channels = set()
        declared_count = None
        header_phase = True
        invalid_count = 0
        examples = []
        try:
            with Path(file_path).open("r", encoding="utf-8-sig") as log:
                for line_number, line in enumerate(log, 1):
                    stripped = line.strip()
                    if header_phase and stripped.startswith("$"):
                        if match := _CHANNEL_COUNT.fullmatch(stripped):
                            declared_count = int(match[1])
                        elif match := _CHANNEL_BUS.fullmatch(stripped):
                            declared_channels.add(int(match[1]))
                        continue
                    if not stripped or stripped.startswith(("#", "$", ";", "//")):
                        continue
                    if header_phase and _CAN_MARKER.search(line):
                        header_phase = False
                    try:
                        message = self.parse_line(line)
                    except ValueError as error:
                        invalid_count += 1
                        if len(examples) < 5:
                            examples.append(f"line {line_number}: {str(error)[:200]}")
                        continue
                    if message is not None:
                        observed.add(message["channel"])
                        yield message
        except UnicodeDecodeError as error:
            raise ValueError(f"Cannot decode DSA-TEXT log '{file_path}' as UTF-8: {error}") from error
        if invalid_count:
            _LOGGER.warning("%s: skipped %d malformed or unsupported CAN records; %s",
                            file_path, invalid_count, "; ".join(examples))
        if ((declared_count is not None and declared_count != len(observed))
                or (declared_channels and declared_channels != observed)):
            _LOGGER.warning("%s: header channel metadata disagrees with observed CAN channels %s; "
                            "using valid CAN records", file_path, sorted(observed))
        if not observed:
            raise ValueError("No valid classic CAN frames found in the DSA-TEXT log.")

    def get_channels(self, file_path: str | Path) -> list[int]:
        return sorted({message["channel"] for message in self._iter_messages(file_path)})

    def load_messages(self, file_path: str | Path, channel: int | None = None) -> list[dict]:
        messages = [message for message in self._iter_messages(file_path)
                    if channel is None or message["channel"] == channel]
        if channel is not None and not messages:
            raise ValueError(f"Selected Diagnostic Channel {channel} was not found in the DSA-TEXT log.")
        return messages
