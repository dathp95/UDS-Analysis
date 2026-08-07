from pathlib import Path
import shutil


PROJECT = Path(__file__).resolve().parent

DIST = PROJECT / "dist" / "EEIV Diagnostic"

DIST.mkdir(
    parents=True,
    exist_ok=True,
)


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
    "output/Reports",
    "output/Logs",
    "output/Temp",
    "output/Cache",
]


for folder in OUTPUT_FOLDERS:

    (DIST / folder).mkdir(
        parents=True,
        exist_ok=True
    )


print()
print("[BUILD RELEASE] Completed")
print(f"[BUILD RELEASE] Output: {DIST}")