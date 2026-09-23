from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from config.paths import Q_CURRENT_DATABASE_FILE


DATABASE_FILE = Q_CURRENT_DATABASE_FILE
SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}
REQUIRED_COLUMNS = {"time", "current"}


@dataclass(frozen=True)
class SleepCurrentDataset:
    id: int
    name: str
    source_file: str | None
    imported_at: str


@dataclass(frozen=True)
class CurrentSample:
    id: int
    dataset_id: int
    time: str
    current: float


@dataclass(frozen=True)
class DatasetImportResult:
    dataset: SleepCurrentDataset
    row_count: int


def resolve_database_path(database_file: str | Path | None = None) -> Path:
    if database_file is None:
        return DATABASE_FILE
    return Path(database_file).expanduser().resolve()


def initialize_database(database_file: str | Path | None = None) -> Path:
    database_path = resolve_database_path(database_file)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with closing(_connect(database_path)) as connection:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    source_file TEXT,
                    imported_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS current_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER NOT NULL,
                    time TEXT NOT NULL,
                    current REAL NOT NULL,
                    FOREIGN KEY (dataset_id)
                        REFERENCES datasets(id)
                        ON DELETE CASCADE
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_current_samples_dataset_id
                    ON current_samples(dataset_id)
                """
            )

    return database_path


def list_datasets(
    database_file: str | Path | None = None,
) -> list[SleepCurrentDataset]:
    initialize_database(database_file)
    with closing(_connect(resolve_database_path(database_file))) as connection:
        rows = connection.execute(
            """
            SELECT id, name, source_file, imported_at
            FROM datasets
            ORDER BY imported_at DESC, id DESC
            """
        ).fetchall()
    return [_dataset_from_row(row) for row in rows]


def get_dataset_by_name(
    name: str,
    database_file: str | Path | None = None,
) -> SleepCurrentDataset | None:
    initialize_database(database_file)
    with closing(_connect(resolve_database_path(database_file))) as connection:
        row = connection.execute(
            """
            SELECT id, name, source_file, imported_at
            FROM datasets
            WHERE name = ?
            """,
            (name,),
        ).fetchone()
    return _dataset_from_row(row) if row else None


def get_samples(
    dataset_id: int,
    database_file: str | Path | None = None,
) -> list[CurrentSample]:
    initialize_database(database_file)
    with closing(_connect(resolve_database_path(database_file))) as connection:
        rows = connection.execute(
            """
            SELECT id, dataset_id, time, current
            FROM current_samples
            WHERE dataset_id = ?
            ORDER BY id
            """,
            (dataset_id,),
        ).fetchall()
    return [
        CurrentSample(
            id=int(row["id"]),
            dataset_id=int(row["dataset_id"]),
            time=str(row["time"]),
            current=float(row["current"]),
        )
        for row in rows
    ]


def read_current_rows(source_path: str | Path) -> list[tuple[str, float]]:
    source = _validate_source_file(source_path)
    frame = _read_source_frame(source)
    normalized = _normalize_source_frame(frame)
    return list(normalized)


def default_dataset_name(source_path: str | Path) -> str:
    return Path(source_path).expanduser().resolve().stem


def import_dataset(
    name: str,
    source_file: str | Path,
    rows: Iterable[tuple[str, float]],
    database_file: str | Path | None = None,
) -> DatasetImportResult:
    database_path = initialize_database(database_file)
    normalized_rows = _normalize_rows(rows)
    if not normalized_rows:
        raise ValueError("Current data file is empty")

    source_path = str(Path(source_file).expanduser().resolve())
    imported_at = _timestamp()

    with closing(_connect(database_path)) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO datasets (name, source_file, imported_at)
                VALUES (?, ?, ?)
                """,
                (name, source_path, imported_at),
            )
            dataset_id = int(cursor.lastrowid)
            _insert_samples(connection, dataset_id, normalized_rows)

    dataset = SleepCurrentDataset(dataset_id, name, source_path, imported_at)
    return DatasetImportResult(dataset=dataset, row_count=len(normalized_rows))


def replace_dataset(
    dataset_id: int,
    name: str,
    source_file: str | Path,
    rows: Iterable[tuple[str, float]],
    database_file: str | Path | None = None,
) -> DatasetImportResult:
    database_path = initialize_database(database_file)
    normalized_rows = _normalize_rows(rows)
    if not normalized_rows:
        raise ValueError("Current data file is empty")

    source_path = str(Path(source_file).expanduser().resolve())
    imported_at = _timestamp()

    with closing(_connect(database_path)) as connection:
        with connection:
            existing = connection.execute(
                "SELECT id FROM datasets WHERE id = ?",
                (dataset_id,),
            ).fetchone()
            if existing is None:
                raise ValueError("Dataset does not exist")

            connection.execute(
                """
                UPDATE datasets
                SET name = ?, source_file = ?, imported_at = ?
                WHERE id = ?
                """,
                (name, source_path, imported_at, dataset_id),
            )
            connection.execute(
                "DELETE FROM current_samples WHERE dataset_id = ?",
                (dataset_id,),
            )
            _insert_samples(connection, dataset_id, normalized_rows)

    dataset = SleepCurrentDataset(dataset_id, name, source_path, imported_at)
    return DatasetImportResult(dataset=dataset, row_count=len(normalized_rows))


def _connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _validate_source_file(source_path: str | Path) -> Path:
    source = Path(source_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Current data file does not exist: {source}")
    if not source.is_file():
        raise ValueError(f"Current data path is not a file: {source}")
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("Q current import only supports .csv and .xlsx files")
    return source


def _read_source_frame(source: Path) -> pd.DataFrame:
    if source.suffix.lower() == ".csv":
        return pd.read_csv(source)
    return pd.read_excel(source)


def _normalize_source_frame(frame: pd.DataFrame) -> list[tuple[str, float]]:
    if frame.empty:
        raise ValueError("Current data file is empty")

    cleaned_frame = frame.replace(r"^\s*$", pd.NA, regex=True).dropna(how="all")
    if cleaned_frame.empty:
        raise ValueError("Current data file is empty")

    columns = {str(column).strip().lower(): column for column in cleaned_frame.columns}
    missing = sorted(REQUIRED_COLUMNS - set(columns))
    if missing:
        raise ValueError(
            "Current data file is missing required column(s): "
            + ", ".join(missing)
        )

    time_values = cleaned_frame[columns["time"]]
    current_values = pd.to_numeric(
        cleaned_frame[columns["current"]],
        errors="coerce",
    )

    invalid_time = time_values.isna() | time_values.astype(str).str.strip().eq("")
    if invalid_time.any():
        raise ValueError("Current data contains empty time values")

    if current_values.isna().any():
        raise ValueError("Current data contains non-numeric current values")

    return [
        (str(time_value).strip(), float(current_value))
        for time_value, current_value in zip(time_values, current_values)
    ]


def _normalize_rows(rows: Iterable[tuple[str, float]]) -> list[tuple[str, float]]:
    normalized_rows: list[tuple[str, float]] = []
    for time_value, current_value in rows:
        time_text = str(time_value).strip()
        if not time_text:
            raise ValueError("Current data contains empty time values")
        normalized_rows.append((time_text, float(current_value)))
    return normalized_rows


def _insert_samples(
    connection: sqlite3.Connection,
    dataset_id: int,
    rows: list[tuple[str, float]],
) -> None:
    connection.executemany(
        """
        INSERT INTO current_samples (dataset_id, time, current)
        VALUES (?, ?, ?)
        """,
        [(dataset_id, time_value, current_value) for time_value, current_value in rows],
    )


def _dataset_from_row(row: sqlite3.Row) -> SleepCurrentDataset:
    return SleepCurrentDataset(
        id=int(row["id"]),
        name=str(row["name"]),
        source_file=row["source_file"],
        imported_at=str(row["imported_at"]),
    )


def _timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")
