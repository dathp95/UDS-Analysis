from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

from config.paths import Q_CURRENT_DATABASE_FILE
from core.q_current_column_detection import (
    CURRENT_COLUMN_KEYWORDS,
    TIME_COLUMN_KEYWORDS,
    AmbiguousColumnError,
    MissingColumnError,
    _find_column,
)

DATABASE_FILE = Q_CURRENT_DATABASE_FILE
SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}
EXPECTED_SAMPLE_COLUMNS = ["id", "dataset_id", "time", "current_A", "current_mA"]


@dataclass(frozen=True)
class SleepCurrentDataset:
    id: int
    name: str
    source_file: str | None
    imported_at: str
    detected_channel: str | None = None


@dataclass(frozen=True)
class CurrentSample:
    id: int
    dataset_id: int
    time: str
    current_A: float
    current_mA: float


@dataclass(frozen=True)
class NormalizedCurrentData:
    rows: list[tuple[str, float, float]]
    detected_channel: str


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
            _ensure_datasets_table(connection)
            _ensure_current_samples_table(connection)
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
            SELECT id, name, source_file, imported_at, detected_channel
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
            SELECT id, name, source_file, imported_at, detected_channel
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
            SELECT id, dataset_id, time, current_A, current_mA
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
            current_A=float(row["current_A"]),
            current_mA=float(row["current_mA"]),
        )
        for row in rows
    ]


def normalize_current_data(source_path: str | Path) -> NormalizedCurrentData:
    source = _validate_source_file(source_path)
    frame = _read_source_frame(source)
    rows, detected_channel = _normalize_source_frame(frame)
    return NormalizedCurrentData(rows=rows, detected_channel=detected_channel)


def read_current_rows(source_path: str | Path) -> list[tuple[str, float, float]]:
    return normalize_current_data(source_path).rows


def default_dataset_name(source_path: str | Path) -> str:
    return Path(source_path).expanduser().resolve().stem


def import_dataset(
    name: str,
    source_file: str | Path,
    rows: Iterable[tuple[str, float, float]],
    database_file: str | Path | None = None,
    detected_channel: str | None = None,
) -> DatasetImportResult:
    database_path = initialize_database(database_file)
    normalized_rows = _normalize_rows(rows)
    if not normalized_rows:
        raise ValueError("Current data file contains no valid measurement rows")

    source_path = str(Path(source_file).expanduser().resolve())
    imported_at = _timestamp()

    with closing(_connect(database_path)) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO datasets (name, source_file, imported_at, detected_channel)
                VALUES (?, ?, ?, ?)
                """,
                (name, source_path, imported_at, detected_channel),
            )
            dataset_id = int(cursor.lastrowid)
            _insert_samples(connection, dataset_id, normalized_rows)

    dataset = SleepCurrentDataset(
        dataset_id,
        name,
        source_path,
        imported_at,
        detected_channel,
    )
    return DatasetImportResult(dataset=dataset, row_count=len(normalized_rows))


def replace_dataset(
    dataset_id: int,
    name: str,
    source_file: str | Path,
    rows: Iterable[tuple[str, float, float]],
    database_file: str | Path | None = None,
    detected_channel: str | None = None,
) -> DatasetImportResult:
    database_path = initialize_database(database_file)
    normalized_rows = _normalize_rows(rows)
    if not normalized_rows:
        raise ValueError("Current data file contains no valid measurement rows")

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
                SET name = ?, source_file = ?, imported_at = ?, detected_channel = ?
                WHERE id = ?
                """,
                (name, source_path, imported_at, detected_channel, dataset_id),
            )
            connection.execute(
                "DELETE FROM current_samples WHERE dataset_id = ?",
                (dataset_id,),
            )
            _insert_samples(connection, dataset_id, normalized_rows)

    dataset = SleepCurrentDataset(
        dataset_id,
        name,
        source_path,
        imported_at,
        detected_channel,
    )
    return DatasetImportResult(dataset=dataset, row_count=len(normalized_rows))


def _ensure_datasets_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            source_file TEXT,
            imported_at TEXT NOT NULL,
            detected_channel TEXT
        )
        """
    )
    dataset_columns = _table_columns(connection, "datasets")
    if "detected_channel" not in dataset_columns:
        connection.execute("ALTER TABLE datasets ADD COLUMN detected_channel TEXT")


def _ensure_current_samples_table(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "current_samples"):
        _create_current_samples_table(connection)
        return

    sample_columns = _table_columns(connection, "current_samples")
    if sample_columns == EXPECTED_SAMPLE_COLUMNS:
        return

    connection.execute("ALTER TABLE current_samples RENAME TO current_samples_legacy")
    _create_current_samples_table(connection)
    legacy_columns = _table_columns(connection, "current_samples_legacy")
    if {"id", "dataset_id", "time", "current"}.issubset(legacy_columns):
        connection.execute(
            """
            INSERT INTO current_samples (id, dataset_id, time, current_A, current_mA)
            SELECT id, dataset_id, time, current, current * 1000.0
            FROM current_samples_legacy
            WHERE time IS NOT NULL AND current IS NOT NULL
            """
        )
    elif {"id", "dataset_id", "time", "current_A", "current_mA"}.issubset(
        legacy_columns
    ):
        connection.execute(
            """
            INSERT INTO current_samples (id, dataset_id, time, current_A, current_mA)
            SELECT id, dataset_id, time, current_A, current_mA
            FROM current_samples_legacy
            WHERE time IS NOT NULL AND current_A IS NOT NULL AND current_mA IS NOT NULL
            """
        )
    connection.execute("DROP TABLE current_samples_legacy")


def _create_current_samples_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE current_samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER NOT NULL,
            time TEXT NOT NULL,
            current_A REAL NOT NULL,
            current_mA REAL NOT NULL,
            FOREIGN KEY (dataset_id)
                REFERENCES datasets(id)
                ON DELETE CASCADE
        )
        """
    )


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def _table_columns(connection: sqlite3.Connection, table_name: str) -> list[str]:
    return [
        str(row["name"])
        for row in connection.execute(f"PRAGMA table_info({table_name})")
    ]


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
        return pd.read_csv(source, dtype=str)
    return pd.read_excel(source, dtype=str)


def _normalize_source_frame(
    frame: pd.DataFrame,
) -> tuple[list[tuple[str, float, float]], str]:
    if frame.empty:
        raise ValueError("Current data file is empty")

    cleaned_frame = frame.replace(r"^\s*$", pd.NA, regex=True).dropna(how="all")
    if cleaned_frame.empty:
        raise ValueError("Current data file is empty")

    time_column = _detect_time_column(cleaned_frame.columns)
    current_column = _detect_current_column(cleaned_frame.columns)

    rows: list[tuple[str, float, float]] = []
    for _index, row in cleaned_frame.iterrows():
        time_text = _normalize_time_value(row[time_column])
        current_A = _parse_current_value(row[current_column])
        if time_text is None or current_A is None:
            continue
        rows.append((time_text, current_A, current_A * 1000.0))

    if not rows:
        raise ValueError("Current data file contains no valid measurement rows")

    return rows, str(current_column).strip()


def _detect_time_column(columns: Iterable[object]) -> object:
    try:
        return _find_column(columns, TIME_COLUMN_KEYWORDS)
    except MissingColumnError as error:
        raise ValueError(
            "Current data file is missing a time column matching keyword(s): "
            + ", ".join(error.keywords)
        ) from error
    except AmbiguousColumnError as error:
        raise ValueError(
            "Multiple time columns detected: " + ", ".join(error.candidates)
        ) from error


def _detect_current_column(columns: Iterable[object]) -> object:
    try:
        return _find_column(columns, CURRENT_COLUMN_KEYWORDS)
    except MissingColumnError as error:
        raise ValueError(
            "Current data file is missing a current column matching keyword(s): "
            + ", ".join(error.keywords)
        ) from error
    except AmbiguousColumnError as error:
        raise ValueError(
            "Multiple current columns detected: " + ", ".join(error.candidates)
        ) from error


def _normalize_time_value(value: object) -> str | None:
    if pd.isna(value):
        return None
    time_text = str(value).strip()
    return time_text or None


def _parse_current_value(value: object) -> float | None:
    if pd.isna(value):
        return None
    current_text = str(value).strip()
    if not current_text:
        return None
    try:
        return float(current_text)
    except ValueError:
        return None


def _normalize_rows(
    rows: Iterable[tuple[str, float, float]],
) -> list[tuple[str, float, float]]:
    normalized_rows: list[tuple[str, float, float]] = []
    for time_value, current_A, current_mA in rows:
        time_text = str(time_value).strip()
        if not time_text:
            raise ValueError("Current data contains empty time values")
        normalized_rows.append((time_text, float(current_A), float(current_mA)))
    return normalized_rows


def _insert_samples(
    connection: sqlite3.Connection,
    dataset_id: int,
    rows: list[tuple[str, float, float]],
) -> None:
    connection.executemany(
        """
        INSERT INTO current_samples (dataset_id, time, current_A, current_mA)
        VALUES (?, ?, ?, ?)
        """,
        [
            (dataset_id, time_value, current_A, current_mA)
            for time_value, current_A, current_mA in rows
        ],
    )


def _dataset_from_row(row: sqlite3.Row) -> SleepCurrentDataset:
    return SleepCurrentDataset(
        id=int(row["id"]),
        name=str(row["name"]),
        source_file=row["source_file"],
        imported_at=str(row["imported_at"]),
        detected_channel=row["detected_channel"],
    )


def _timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")
