from pathlib import Path
import sys

if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).resolve().parent
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_DIR = PROJECT_ROOT / "output"

REPORT_DIR = OUTPUT_DIR / "Reports"
LOG_DIR = OUTPUT_DIR / "Logs"
TEMP_DIR = OUTPUT_DIR / "Temp"
CACHE_DIR = OUTPUT_DIR / "Cache"



CONFIG_DIR = PROJECT_ROOT / "config"
EXPORT_CODING_FILES_DIR = CONFIG_DIR / "export_coding_files"

VEHICLES_DIR = CONFIG_DIR / "vehicles"

QUICK_FILTER_FILE = CONFIG_DIR / "quick_filters.json"
SHORTCUTS_FILE = PROJECT_ROOT / "shortcuts" / "shortcuts.json"
DISPLAY_NAMES_FILE = CONFIG_DIR / "display_names.json"
UDS_SERVICES_FILE = CONFIG_DIR / "uds_services.json"
UDS_USER_FILE = CONFIG_DIR / "uds_user.json"

if getattr(sys, "frozen", False):
    RESOURCE_ROOT = Path(sys._MEIPASS)
else:
    RESOURCE_ROOT = PROJECT_ROOT

RESOURCE_DIR = RESOURCE_ROOT / "gui" / "resources"
ICON_DIR = RESOURCE_DIR / "icons"
IMAGE_DIR = RESOURCE_DIR / "images"
