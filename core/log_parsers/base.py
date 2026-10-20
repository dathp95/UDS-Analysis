from abc import ABC, abstractmethod
from pathlib import Path

from core.log_parsers.diagnostics import ParserDiagnostics


HEADER_LIMIT = 8192


def read_text_header(file_path: str | Path) -> str:
    """Read a bounded UTF-8 prefix, accepting a leading UTF-8 BOM."""
    try:
        with Path(file_path).open("r", encoding="utf-8-sig") as log:
            return log.read(HEADER_LIMIT)
    except UnicodeDecodeError as error:
        raise ValueError(f"Cannot decode TXT log '{file_path}' as UTF-8: {error}") from error


class BaseTextLogParser(ABC):
    """File errors propagate; invalid individual records may be diagnosed and skipped.

    Messages contain timestamp (seconds), channel (native integer), can_id,
    dlc, and data (a list of CAN bytes, including padding).
    """

    @abstractmethod
    def can_parse(self, header: str) -> bool:
        """Identify this format from a bounded file prefix."""

    @abstractmethod
    def get_channels(self, file_path: str | Path, *, diagnostics: ParserDiagnostics | None = None) -> list[int]:
        """Return sorted unique channels from valid CAN records."""

    @abstractmethod
    def load_messages(self, file_path: str | Path, channel: int | None = None,
                      *, diagnostics: ParserDiagnostics | None = None) -> list[dict]:
        """Load normalized messages, raising when no valid/selected channel exists."""
