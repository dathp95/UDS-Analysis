from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from config.paths import Q_CURRENT_REPORT_DIR


QCURRENT_REPORT_DIR = Q_CURRENT_REPORT_DIR
SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}
TIME_ALIASES = {
    "time",
    "timestamp",
    "times",
    "timems",
    "timemillis",
    "timemilliseconds",
    "timesec",
    "timesecond",
    "timeseconds",
    "seconds",
    "second",
    "t",
}
CURRENT_ALIASES = {
    "current",
    "currentma",
    "currentmilliamps",
    "currentmilliamp",
    "currenta",
    "currentamps",
    "currentamp",
    "ma",
    "imotor",
    "i",
}


@dataclass(frozen=True)
class QCurrentImportResult:
    source_path: Path
    database_path: Path
    row_count: int
    samples: list[dict[str, float]]


def import_q_current_file(source_path: str | Path) -> QCurrentImportResult:
    source = Path(source_path).expanduser().resolve()
    _validate_source_file(source)

    frame = _read_source_frame(source)
    normalized = _normalize_current_frame(frame)
    database_path = _write_sqlite_database(source, normalized)

    return QCurrentImportResult(
        source_path=source,
        database_path=database_path,
        row_count=len(normalized),
        samples=normalized.to_dict("records"),
    )


def _validate_source_file(source: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Current data file does not exist: {source}")

    if not source.is_file():
        raise ValueError(f"Current data path is not a file: {source}")

    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("Q current import only supports .csv and .xlsx files")


def _read_source_frame(source: Path) -> pd.DataFrame:
    if source.suffix.lower() == ".csv":
        return pd.read_csv(source)

    return pd.read_excel(source)


def _normalize_current_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        raise ValueError("Current data file is empty")

    columns = {
        _normalize_column_name(column): column
        for column in frame.columns
    }
    time_column = _find_required_column(columns, TIME_ALIASES, "time")
    current_column = _find_required_column(
        columns,
        CURRENT_ALIASES,
        "current_ma",
    )

    normalized = pd.DataFrame({
        "time": pd.to_numeric(frame[time_column], errors="coerce"),
        "current_ma": pd.to_numeric(frame[current_column], errors="coerce"),
    })
    if normalized[["time", "current_ma"]].isna().any().any():
        raise ValueError("Current data contains non-numeric time/current values")

    return normalized.reset_index(drop=True)


def _normalize_column_name(column: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(column).strip().lower())


def _find_required_column(
    columns: dict[str, Any],
    aliases: set[str],
    display_name: str,
) -> Any:
    for alias in aliases:
        if alias in columns:
            return columns[alias]

    raise ValueError(
        f"Current data file is missing required column: {display_name}"
    )


def _write_sqlite_database(source: Path, frame: pd.DataFrame) -> Path:
    output_dir = QCURRENT_REPORT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    database_path = output_dir / f"{_safe_stem(source.stem)}_{timestamp}.db"

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute(
            """
            CREATE TABLE current_samples (
                row_index INTEGER PRIMARY KEY,
                time REAL NOT NULL,
                current_ma REAL NOT NULL
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO current_samples (row_index, time, current_ma)
            VALUES (?, ?, ?)
            """,
            [
                (index, float(row.time), float(row.current_ma))
                for index, row in frame.iterrows()
            ],
        )
        connection.execute(
            """
            CREATE TABLE import_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        metadata = {
            "source_path": str(source),
            "source_name": source.name,
            "source_extension": source.suffix.lower(),
            "imported_at": datetime.now().isoformat(timespec="seconds"),
            "row_count": str(len(frame)),
        }
        connection.executemany(
            "INSERT INTO import_metadata (key, value) VALUES (?, ?)",
            metadata.items(),
        )
        connection.commit()

    return database_path


def _safe_stem(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
    return safe or "q_current"