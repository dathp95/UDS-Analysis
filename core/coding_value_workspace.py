from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import uuid


@dataclass
class CodingEcuWorkspace:
    id: str
    name: str
    coding_file: str = ""

    def __post_init__(self):
        self.id = _normalize_required_text(self.id, "Workspace id")
        self.name = _normalize_required_text(self.name, "Workspace name")
        self.coding_file = _normalize_optional_text(self.coding_file)

    @classmethod
    def create(
            cls,
            name: str,
            coding_file: str = "",
        ) -> "CodingEcuWorkspace":
        return cls(
            id=uuid.uuid4().hex,
            name=name,
            coding_file=coding_file,
        )

    def rename(self, name: str) -> None:
        self.name = _normalize_required_text(name, "Workspace name")

    def set_coding_file(self, coding_file: str) -> None:
        self.coding_file = _normalize_optional_text(coding_file)

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "name": self.name,
            "coding_file": self.coding_file,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CodingEcuWorkspace":
        return cls(
            id=payload.get("id", ""),
            name=payload.get("name", ""),
            coding_file=payload.get("coding_file", ""),
        )


def _normalize_required_text(value: str, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} cannot be empty.")

    return text


def _normalize_optional_text(value: str) -> str:
    return str(value or "").strip()
