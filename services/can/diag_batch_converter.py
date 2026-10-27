
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BatchConvertResult:
    imported: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)


def convert_diag_folder(
    source_folder: str | Path,
    repository,
) -> BatchConvertResult:
    """
    Convert .diag files into native V-CODE .json files.

    - Never modify source .diag files.
    - Never overwrite existing JSON files.
    - Continue processing if one source fails.
    - Preserve original CAN IDs through the existing parser.
    """
    source = Path(source_folder).resolve()
    destination_root = repository.root.resolve()

    if not source.is_dir():
        raise ValueError("Selected DIAG folder does not exist.")

    if source == destination_root:
        raise ValueError(
            "Select an external source folder, not the "
            "V-CODE diagnostic_sequences folder."
        )

    result = BatchConvertResult()

    files = sorted(
        (
            path
            for path in source.iterdir()
            if path.is_file()
            and path.suffix.lower() == ".diag"
        ),
        key=lambda path: path.name.casefold(),
    )

    destination_root.mkdir(parents=True, exist_ok=True)

    # Windows filenames are case-insensitive in typical setups.
    reserved_names = {
        path.name.casefold()
        for path in destination_root.iterdir()
        if path.is_file()
    }

    for diag_path in files:
        destination = (
            destination_root / f"{diag_path.stem}.json"
        )

        if destination.name.casefold() in reserved_names:
            result.skipped.append(diag_path.name)
            continue

        created = False

        try:
            case = repository.fn_load_sequence(diag_path)
            normalized = repository._normalize_test_case(case)

            import json

            content = json.dumps(
                repository._test_case_to_json(normalized),
                ensure_ascii=False,
                indent=4,
            )

            # Validate JSON syntax before file creation.
            json.loads(content)

            # "x" means create exclusively; never overwrite.
            with destination.open("x", encoding="utf-8") as stream:
                created = True
                stream.write(content)

            # Check schema by reading the generated document.
            repository.fn_load_sequence(destination)

            reserved_names.add(destination.name.casefold())
            result.imported.append(destination.name)

        except FileExistsError:
            result.skipped.append(diag_path.name)

        except (OSError, ValueError, UnicodeError) as error:
            if created:
                destination.unlink(missing_ok=True)

            result.failed.append(
                (diag_path.name, str(error))
            )
    return result
