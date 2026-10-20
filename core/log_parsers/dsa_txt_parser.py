import logging
import re
from collections.abc import Iterator
from pathlib import Path

from core.log_parsers.base import BaseTextLogParser, read_text_header
from core.log_parsers.diagnostics import ParserDiagnostics


_LOGGER = logging.getLogger(__name__)
_SIGNATURE = re.compile(r"^[ \t]*#!DSAVci\.log[ \t\r]*$", re.MULTILINE)
_FORMAT = re.compile(r"^[ \t]*\$Log\.Format\.String[ \t]*=[ \t]*DSA-TEXT[ \t\r]*$", re.MULTILINE)
_CHANNEL_COUNT = re.compile(r"\$Log\.Channels\s*=\s*([0-9]+)\s*$")
_CHANNEL_BUS = re.compile(r"\$Log\.Ch([0-9]+)\.BusType\s*=\s*CAN(?:_[A-Z0-9]+)?\s*$")
_BUS_TYPE = re.compile(r"\$Log\.Ch([0-9]+)\.BusType\s*=\s*(CAN|CAN_HS|CAN_LS|CAN_FD|LIN)\s*$")
_BAUD_RATE = re.compile(r"\$Log\.Ch([0-9]+)\.BaudRate\s*=\s*([0-9]+)(?:\s*\[Baud\])?\s*$")
_CAN_MARKER = re.compile(r"\bCh[^\s()]+\s*\(\s*CAN\s*\)", re.IGNORECASE)
_BUS_MARKER = re.compile(r"\bCh[^\s()]*\s*\(\s*([A-Z0-9_]+)\s*\)", re.IGNORECASE)
_CAN_HINT = re.compile(r"\bMsg\b.*\bid:\s*0x", re.IGNORECASE)
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


class CANRecordError(ValueError):
    """A parser-owned, payload-free description of an invalid CAN record."""


class UnsupportedCANRecord(CANRecordError):
    pass


def _is_can_record(line: str) -> bool:
    if _CAN_MARKER.search(line):
        return True
    bus = _BUS_MARKER.search(line)
    if bus is not None and not bus[1].upper().startswith("CAN"):
        return False
    return bool(_CAN_HINT.search(line))


class DSATextParser(BaseTextLogParser):
    """DSA-TEXT V1: verified classic CAN 11n records, native channel numbering."""

    def can_parse(self, header: str) -> bool:
        header = header.lstrip("\ufeff")
        return bool(_SIGNATURE.search(header) and _FORMAT.search(header))

    def parse_line(self, line: str) -> dict | None:
        """Ignore non-CAN records; raise ValueError for malformed CAN records."""
        if not _CAN_MARKER.search(line):
            if _is_can_record(line):
                bus = _BUS_MARKER.search(line)
                if bus is not None and bus[1].upper() != "CAN":
                    raise UnsupportedCANRecord("Unsupported CAN bus record")
                raise CANRecordError("Missing or invalid CAN channel marker")
            return None
        if not _MSG_MARKER.search(line):
            if line.lstrip().startswith("[") and "id:" in line.lower():
                raise CANRecordError("Malformed CAN record: missing Msg marker")
            return None
        match = _FRAME.fullmatch(line)
        if match is None:
            raise CANRecordError("Malformed CAN record or timestamp")
        fields = match.groupdict()
        if fields["frame_type"].lower() != "11n":
            raise UnsupportedCANRecord("Unsupported CAN frame type (V1 supports classic CAN 11n)")
        minutes, seconds = int(fields["minutes"]), int(fields["seconds"])
        if minutes >= 60 or seconds >= 60:
            raise CANRecordError("Invalid timestamp: minutes and seconds must be 00-59")
        can_id = int(fields["can_id"], 16)
        if can_id > 0x1FFFFFFF:
            raise CANRecordError("CAN ID exceeds the 29-bit CAN range")
        if can_id > 0x7FF:
            raise CANRecordError("CAN ID exceeds the 11-bit range for an 11n record")
        dlc = int(fields["dlc"])
        if not 0 <= dlc <= 8:
            raise CANRecordError("Classic CAN DLC must be 0-8")
        tokens = fields["data"].split()
        if len(tokens) != dlc:
            raise CANRecordError(f"DLC mismatch: declared {dlc}, found {len(tokens)} bytes")
        if any(_BYTE.fullmatch(token) is None for token in tokens):
            raise CANRecordError("Invalid hexadecimal CAN data byte")
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

    def _iter_messages(self, file_path: str | Path, diagnostics: ParserDiagnostics) -> Iterator[dict]:
        if not self.can_parse(read_text_header(file_path)):
            raise ValueError("Invalid DSA-TEXT header: both DSA signatures are required.")
        header_phase = True
        try:
            with Path(file_path).open("r", encoding="utf-8-sig") as log:
                for line_number, line in enumerate(log, 1):
                    stripped = line.strip()
                    if header_phase and stripped.startswith("$"):
                        if match := _CHANNEL_COUNT.fullmatch(stripped):
                            diagnostics.declared_channel_count = int(match[1])
                        if match := _CHANNEL_BUS.fullmatch(stripped):
                            diagnostics.declared_channels.append(int(match[1]))
                        if match := _BUS_TYPE.fullmatch(stripped):
                            diagnostics.bus_types[int(match[1])] = match[2]
                        if match := _BAUD_RATE.fullmatch(stripped):
                            diagnostics.baud_rates[int(match[1])] = int(match[2])
                        diagnostics.non_can_lines += 1
                        continue
                    if not stripped or stripped.startswith(("#", "$", ";", "//")):
                        diagnostics.non_can_lines += 1
                        continue
                    if not _is_can_record(line):
                        diagnostics.non_can_lines += 1
                        continue
                    header_phase = False
                    diagnostics.total_can_records += 1
                    try:
                        message = self.parse_line(line)
                    except UnsupportedCANRecord as error:
                        diagnostics.unsupported_frames += 1
                        diagnostics.add_example(line_number, str(error))
                        continue
                    except ValueError as error:
                        diagnostics.malformed_frames += 1
                        diagnostics.add_example(line_number, str(error) if isinstance(error, CANRecordError)
                                                else "Invalid numeric CAN field")
                        continue
                    if message is not None:
                        diagnostics.observe(message, line_number)
                        yield message
                    else:
                        diagnostics.other_skipped_can_frames += 1
                        diagnostics.add_example(line_number, "Unrecognized CAN-like record")
        except UnicodeDecodeError as error:
            raise ValueError(f"Cannot decode DSA-TEXT log '{file_path}' as UTF-8: {error}") from error
        diagnostics.declared_channels = sorted(set(diagnostics.declared_channels))
        diagnostics.finish()
        if diagnostics.has_warnings:
            _LOGGER.warning("DSA-TEXT parser diagnostics: %s; %s",
                            " ".join(diagnostics.warnings), "; ".join(diagnostics.examples))
        if not diagnostics.parsed_frames:
            raise ValueError("No valid classic CAN frames found in the DSA-TEXT log.")

    def get_channels(self, file_path: str | Path, *, diagnostics: ParserDiagnostics | None = None) -> list[int]:
        diagnostics = diagnostics if diagnostics is not None else ParserDiagnostics()
        diagnostics.reset()
        for _ in self._iter_messages(file_path, diagnostics):
            pass
        return diagnostics.channels.copy()

    def load_messages(self, file_path: str | Path, channel: int | None = None,
                      *, diagnostics: ParserDiagnostics | None = None) -> list[dict]:
        diagnostics = diagnostics if diagnostics is not None else ParserDiagnostics()
        diagnostics.reset(channel)
        messages = [message for message in self._iter_messages(file_path, diagnostics)
                    if channel is None or message["channel"] == channel]
        diagnostics.loaded_frames = len(messages)
        if channel is not None and not messages:
            raise ValueError(f"Selected Diagnostic Channel {channel} was not found in the DSA-TEXT log.")
        return messages
