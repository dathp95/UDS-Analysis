from pathlib import Path
import os
import sys

if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).resolve().parent
    LICENSE_DIR = PROJECT_ROOT / "license"
else:
    LICENSE_DIR = Path(__file__).resolve().parent

PUBLIC_KEY_PATH = LICENSE_DIR / "public.pem"
LICENSE_FILE_PATH = LICENSE_DIR / "license.lic"

LOCAL_APP_DATA_DIR = Path(
    os.environ.get("LOCALAPPDATA")
    or Path.home() / "AppData" / "Local"
)
ACTIVATION_DIR = LOCAL_APP_DATA_DIR / "V-CODE"
ACTIVATION_FILE_PATH = ACTIVATION_DIR / "activation.dat"
