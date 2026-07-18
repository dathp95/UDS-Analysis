from pathlib import Path
import sys

if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).resolve().parent
    LICENSE_DIR = PROJECT_ROOT / "license"
else:
    LICENSE_DIR = Path(__file__).resolve().parent

PUBLIC_KEY_PATH = LICENSE_DIR / "public.pem"
LICENSE_FILE_PATH = LICENSE_DIR / "license.lic"