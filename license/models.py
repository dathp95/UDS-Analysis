"""

License data model for Python UDS Analyzer.

This module contains only data structures.
No business logic, file I/O or cryptography.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .exceptions import (
    LicenseFormatError,
    LicenseParseError,
)


@dataclass(slots=True)
class License:
    """
    Represents a validated license.
    """

    customer: str
    edition: str
    issue_date: datetime
    expire_date: datetime

    # Reserved for future versions
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """
        Return True if the license has expired.
        """
        return self._now_for(self.expire_date) > self.expire_date

    @property
    def days_remaining(self) -> int:
        """
        Return remaining valid days.

        Returns
        -------
        int
            Positive -> remaining days
            Zero     -> expires today
            Negative -> already expired
        """
        return (self.expire_date - self._now_for(self.expire_date)).days

    @staticmethod
    def _now_for(value: datetime) -> datetime:
        if value.tzinfo is None:
            return datetime.now()

        return datetime.now(UTC)

    @property
    def status(self) -> str:
        """
        Human readable license status.
        """
        return "Expired" if self.is_expired else "Valid"

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the model into a JSON serializable dictionary.
        """

        return {
            "customer": self.customer,
            "edition": self.edition,
            "issue_date": self.issue_date.isoformat(timespec="seconds"),
            "expire_date": self.expire_date.isoformat(timespec="seconds"),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "License":
        """
        Create a License object from dictionary.

        Raises
        ------
        LicenseFormatError
            Missing or invalid required fields.

        LicenseParseError
            Invalid datetime format.
        """

        required_fields = (
            "customer",
            "edition",
            "issue_date",
            "expire_date",
        )

        missing_fields = [
            field
            for field in required_fields
            if field not in data
        ]

        if missing_fields:
            raise LicenseFormatError(
                f"Missing required field(s): "
                f"{', '.join(missing_fields)}"
            )

        customer = data["customer"]
        edition = data["edition"]
        metadata = data.get("metadata", {})

        if not isinstance(customer, str) or not customer.strip():
            raise LicenseFormatError(
                "customer must be a non-empty string."
            )

        if not isinstance(edition, str) or not edition.strip():
            raise LicenseFormatError(
                "edition must be a non-empty string."
            )

        if not isinstance(metadata, dict):
            raise LicenseFormatError(
                "metadata must be a dictionary."
            )

        try:
            issue_date = datetime.fromisoformat(
                data["issue_date"]
            )

            expire_date = datetime.fromisoformat(
                data["expire_date"]
            )

        except ValueError as ex:
            raise LicenseParseError(
                f"Invalid datetime format: {ex}"
            ) from ex

        return cls(
            customer=customer.strip(),
            edition=edition.strip(),
            issue_date=issue_date,
            expire_date=expire_date,
            metadata=metadata,
        )

    def __str__(self) -> str:
        return (
            f"{self.customer} "
            f"({self.edition}) "
            f"[{self.status}]"
        )

    def __repr__(self) -> str:
        return (
            "License("
            f"customer={self.customer!r}, "
            f"edition={self.edition!r}, "
            f"issue_date={self.issue_date!r}, "
            f"expire_date={self.expire_date!r}, "
            f"metadata={self.metadata!r}"
            ")"
        )
