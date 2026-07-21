from pathlib import Path
import shutil

PROJECT = Path(__file__).parent
DIST = PROJECT / "dist" / "EEIV Diagnostic"

DIST.mkdir(parents=True, exist_ok=True)

# Copy folders
for folder in ["config", "license"]:
    src = PROJECT / folder
    dst = DIST / folder

    if dst.exists():
        shutil.rmtree(dst)

    shutil.copytree(src, dst)

# Copy README
readme = PROJECT / "README.txt"
if readme.exists():
    shutil.copy2(readme, DIST / "README.txt")

# Create output folders
for folder in ["output", "output/Reports", "output/Logs", "output/Temp", "output/Cache"]:
    (DIST / folder).mkdir(parents=True, exist_ok=True)

