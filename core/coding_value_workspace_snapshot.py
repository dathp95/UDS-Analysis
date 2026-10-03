from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CODING_WORKSPACE_SNAPSHOT_VERSION = 1


@dataclass(frozen=True)
class CodingWorkspaceRowSnapshot:
    parameter: str
    byte_pos: str
    bit_pos: str
    bit_length: str
    raw_value: str

    @classmethod
    def from_dict(cls, payload: Any) -> "CodingWorkspaceRowSnapshot":
        if not isinstance(payload, dict):
            raise ValueError("Row snapshot must be an object.")

        return cls(
            parameter=str(payload.get("parameter", "")),
            byte_pos=str(payload.get("byte_pos", "")),
            bit_pos=str(payload.get("bit_pos", "")),
            bit_length=str(payload.get("bit_length", "")),
            raw_value=str(payload.get("raw_value", "")),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "parameter": self.parameter,
            "byte_pos": self.byte_pos,
            "bit_pos": self.bit_pos,
            "bit_length": self.bit_length,
            "raw_value": self.raw_value,
        }


@dataclass(frozen=True)
class CodingWorkspaceSnapshot:
    coding_file: str = ""
    payload_input: str = ""
    payload_preview: str = ""
    baseline_payload: str = ""
    parameter_filter: str = ""
    checked: bool = False
    raw_values: tuple[CodingWorkspaceRowSnapshot, ...] = ()
    working_log: str = ""

    @classmethod
    def from_dict(cls, payload: Any) -> "CodingWorkspaceSnapshot":
        if not isinstance(payload, dict):
            raise ValueError("Snapshot must be an object.")
        if payload.get("version") != CODING_WORKSPACE_SNAPSHOT_VERSION:
            raise ValueError("Unsupported snapshot version.")

        raw_rows = payload.get("raw_values", [])
        if not isinstance(raw_rows, list):
            raise ValueError("Snapshot raw_values must be a list.")

        return cls(
            coding_file=str(payload.get("coding_file", "")),
            payload_input=str(payload.get("payload_input", "")),
            payload_preview=str(payload.get("payload_preview", "")),
            baseline_payload=str(payload.get("baseline_payload", "")),
            parameter_filter=str(payload.get("parameter_filter", "")),
            checked=bool(payload.get("checked", False)),
            raw_values=tuple(
                CodingWorkspaceRowSnapshot.from_dict(raw_row)
                for raw_row in raw_rows
            ),
            working_log=str(payload.get("working_log", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": CODING_WORKSPACE_SNAPSHOT_VERSION,
            "coding_file": self.coding_file,
            "payload_input": self.payload_input,
            "payload_preview": self.payload_preview,
            "baseline_payload": self.baseline_payload,
            "parameter_filter": self.parameter_filter,
            "checked": self.checked,
            "raw_values": [
                row.to_dict()
                for row in self.raw_values
            ],
            "working_log": self.working_log,
        }
