from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


TIME_COLUMN_KEYWORDS = [
    "time",
    "trigger time",
    "timestamp",
]

CURRENT_COLUMN_KEYWORDS = [
    "current",
    "average",
    "average current",
]


class ColumnDetectionError(ValueError):
    """Base error for source-column detection failures."""


@dataclass(frozen=True)
class AmbiguousColumnError(ColumnDetectionError):
    keyword: str
    candidates: list[str]

    def __str__(self) -> str:
        return (
            f"Multiple columns match keyword '{self.keyword}': "
            + ", ".join(self.candidates)
        )


class MissingColumnError(ColumnDetectionError):
    def __init__(self, keywords: Iterable[str]):
        self.keywords = list(keywords)
        super().__init__(
            "No source column matched keyword(s): " + ", ".join(self.keywords)
        )


def _normalize_header(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _find_column(columns: Iterable[object], keywords: Iterable[str]) -> object:
    column_pairs = [(_normalize_header(column), column) for column in columns]
    normalized_keywords = [_normalize_header(keyword) for keyword in keywords]

    for keyword in normalized_keywords:
        matches = [column for header, column in column_pairs if header == keyword]
        if matches:
            return _select_single_match(keyword, matches)

    for keyword in normalized_keywords:
        matches = [column for header, column in column_pairs if keyword in header]
        if matches:
            return _select_single_match(keyword, matches)

    raise MissingColumnError(normalized_keywords)


def _select_single_match(keyword: str, matches: list[object]) -> object:
    if len(matches) == 1:
        return matches[0]
    raise AmbiguousColumnError(
        keyword=keyword,
        candidates=[str(match).strip() for match in matches],
    )
