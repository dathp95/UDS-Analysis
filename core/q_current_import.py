from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.sleep_current_database import (
    default_dataset_name,
    import_dataset,
    read_current_rows,
    resolve_database_path,
)


@dataclass(frozen=True)
class QCurrentImportResult:
    source_path: Path
    database_path: Path
    row_count: int
    samples: list[dict[str, float | str]]


def import_q_current_file(source_path: str | Path) -> QCurrentImportResult:
    source = Path(source_path).expanduser().resolve()
    rows = read_current_rows(source)
    result = import_dataset(default_dataset_name(source), source, rows)
    return QCurrentImportResult(
        source_path=source,
        database_path=resolve_database_path(),
        row_count=result.row_count,
        samples=[
            {"time": time_value, "current": current_value}
            for time_value, current_value in rows
        ],
    )
