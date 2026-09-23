from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.sleep_current_database import (
    default_dataset_name,
    import_dataset,
    normalize_current_data,
    resolve_database_path,
)


@dataclass(frozen=True)
class QCurrentImportResult:
    source_path: Path
    database_path: Path
    row_count: int
    detected_channel: str
    samples: list[dict[str, float | str]]


def import_q_current_file(source_path: str | Path) -> QCurrentImportResult:
    source = Path(source_path).expanduser().resolve()
    normalized = normalize_current_data(source)
    result = import_dataset(
        default_dataset_name(source),
        source,
        normalized.rows,
        detected_channel=normalized.detected_channel,
    )
    return QCurrentImportResult(
        source_path=source,
        database_path=resolve_database_path(),
        row_count=result.row_count,
        detected_channel=normalized.detected_channel,
        samples=[
            {
                "time": time_value,
                "current_A": current_A,
                "current_mA": current_mA,
            }
            for time_value, current_A, current_mA in normalized.rows
        ],
    )
