from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CodingValueOption:
    raw_value: str
    label: str


@dataclass(frozen=True)
class CodingValueRow:
    parameter: str
    byte_pos: str
    bit_pos: str
    bit_length: str
    raw_value: str
    decoded_value: str
    decoded_options: tuple[CodingValueOption, ...]


@dataclass(frozen=True)
class CodingDefinition:
    name: str
    rows: tuple[CodingValueRow, ...]
    source_file: str = ""
    source_path: str = ""


def load_coding_value_rows(
        excel_path: str | Path,
        coding_payload: str = "",
    ) -> list[CodingValueRow]:
    from core.coding_value_definition import load_coding_definition_from_excel

    definition = load_coding_definition_from_excel(
        excel_path,
        coding_payload,
    )
    return list(definition.rows)


def load_coding_value_rows_from_json(json_path: str | Path) -> list[CodingValueRow]:
    from core.coding_value_definition import load_coding_definition_from_json

    definition = load_coding_definition_from_json(json_path)
    return list(definition.rows)


def export_coding_value_rows_to_json(
        excel_path: str | Path,
        rows: list[CodingValueRow],
        output_dir: str | Path,
    ) -> Path:
    from core.coding_value_definition import export_coding_definition_to_json

    source_path = Path(excel_path)
    definition = CodingDefinition(
        name=source_path.stem or "coding_value",
        rows=tuple(rows),
        source_file=source_path.name,
        source_path=str(source_path),
    )
    return export_coding_definition_to_json(
        definition,
        output_dir,
    )
