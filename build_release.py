from pathlib import Path
import json
import shutil


PROJECT = Path(__file__).resolve().parent

DIST = PROJECT / "dist" / "EEIV Diagnostic"

DIST.mkdir(
    parents=True,
    exist_ok=True,
)


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


for folder in RUNTIME_FOLDERS:

    src = PROJECT / folder
    dst = DIST / folder

    if not src.exists():

        print(
            f"[WARNING] Folder not found: {src}"
        )

        continue

    if dst.exists():

        shutil.rmtree(dst)

    shutil.copytree(
        src,
        dst
    )

    print(
        f"[COPIED] {folder}"
    )


release_features_file = DIST / "config" / "release_features.json"
release_features_file.parent.mkdir(
    parents=True,
    exist_ok=True,
)
release_features_file.write_text(
    json.dumps(
        {
            "deactivated_features": DEACTIVATED_RELEASE_FEATURES,
        },
        indent=2,
    ),
    encoding="utf-8",
)
print(
    f"[WRITTEN] {release_features_file.relative_to(DIST)}"
)


# ==========================================
# Copy README
# ==========================================

readme = PROJECT / "README.txt"

if readme.exists():

    shutil.copy2(
        readme,
        DIST / "README.txt"
    )


# ==========================================
# Create output folders
# ==========================================

OUTPUT_FOLDERS = [
    "output",
    "output/Report_LogAnalyzer",
    "output/Report_CodingValue",
]


for folder in OUTPUT_FOLDERS:

    (DIST / folder).mkdir(
        parents=True,
        exist_ok=True
    )


print()
print("[BUILD RELEASE] Completed")
print(f"[BUILD RELEASE] Output: {DIST}")
