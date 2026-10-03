import json
import shutil
from argparse import ArgumentParser
from pathlib import Path


PROJECT = Path(__file__).resolve().parent
DIST = PROJECT / "dist" / "EEIV Diagnostic"
ARCHIVE_EXTENSIONS = {
    ".zip",
    ".rar",
    ".7z",
}


# ==========================================
# Release feature flags
# ==========================================

DEACTIVATED_RELEASE_FEATURES = [
    "can_interface",
]


# ==========================================
# Copy runtime folders
# ==========================================

RUNTIME_FOLDERS = [
    "config",
    "license",
    "shortcuts",
]


OUTPUT_FOLDERS = [
    "output",
    "output/Report_LogAnalyzer",
    "output/Report_CodingValue",
    "output/Report_QCurrent",
]


def copy_release_runtime(
        runtime_source: Path,
        dist: Path,
    ) -> None:
    if not runtime_source.exists() or not runtime_source.is_dir():
        raise SystemExit(
            f"[BUILD FAILED] Nuitka runtime folder not found: {runtime_source}"
        )

    if dist.exists():
        shutil.rmtree(dist)

    shutil.copytree(runtime_source, dist)
    print(f"[COPIED] Nuitka runtime: {runtime_source} -> {dist}")


def copy_runtime_folders(
        project: Path,
        dist: Path,
    ) -> None:
    for folder in RUNTIME_FOLDERS:
        src = project / folder
        dst = dist / folder

        if not src.exists():
            print(f"[WARNING] Folder not found: {src}")
            continue

        if dst.exists():
            shutil.rmtree(dst)

        shutil.copytree(src, dst)
        print(f"[COPIED] {folder}")


def write_release_features(dist: Path) -> None:
    release_features_file = dist / "config" / "release_features.json"
    release_features_file.parent.mkdir(parents=True, exist_ok=True)
    release_features_file.write_text(
        json.dumps(
            {
                "deactivated_features": DEACTIVATED_RELEASE_FEATURES,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[WRITTEN] {release_features_file.relative_to(dist)}")


def copy_readme(
        project: Path,
        dist: Path,
    ) -> None:
    readme = project / "README.txt"
    if not readme.exists():
        return

    shutil.copy2(readme, dist / "README.txt")
    print("[COPIED] README.txt")


def create_output_folders(dist: Path) -> None:
    for folder in OUTPUT_FOLDERS:
        (dist / folder).mkdir(parents=True, exist_ok=True)
        print(f"[CREATED] {folder}")


def validate_no_archives(dist: Path) -> None:
    archives = [
        path
        for path in dist.rglob("*")
        if path.is_file() and path.suffix.lower() in ARCHIVE_EXTENSIONS
    ]

    if archives:
        print("[SECURITY] Archive files detected:")
        for path in archives:
            print(f"  - {path.relative_to(dist)}")
        raise SystemExit("[BUILD FAILED] Release contains archive files.")

    print("[SECURITY] PASS - no ZIP/RAR/7Z files detected.")


def prepare_release(
        *,
        project: Path = PROJECT,
        dist: Path = DIST,
        runtime_source: Path | None = None,
        clean: bool = False,
        validate_archives: bool = False,
    ) -> None:
    project = project.resolve()
    dist = dist.resolve()

    if runtime_source is not None:
        copy_release_runtime(runtime_source.resolve(), dist)
    else:
        if clean and dist.exists():
            shutil.rmtree(dist)
        dist.mkdir(parents=True, exist_ok=True)

    copy_runtime_folders(project, dist)
    write_release_features(dist)
    copy_readme(project, dist)
    create_output_folders(dist)

    if validate_archives:
        validate_no_archives(dist)

    print()
    print("[BUILD RELEASE] Completed")
    print(f"[BUILD RELEASE] Output: {dist}")


def parse_args():
    parser = ArgumentParser(
        description="Prepare the V-CODE Windows release directory."
    )
    parser.add_argument(
        "--runtime-source",
        type=Path,
        help="Nuitka standalone .dist folder to normalize into final dist.",
    )
    parser.add_argument(
        "--dist",
        type=Path,
        default=DIST,
        help="Final release directory.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean the final release directory before preparing it.",
    )
    parser.add_argument(
        "--validate-archives",
        action="store_true",
        help="Fail if ZIP/RAR/7Z archives exist in the final release.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prepare_release(
        dist=args.dist,
        runtime_source=args.runtime_source,
        clean=args.clean,
        validate_archives=args.validate_archives,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
