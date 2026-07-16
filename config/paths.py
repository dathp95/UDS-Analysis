from pathlib import Path

PROJECT_ROOT = Path.cwd()

OUTPUT_DIR = PROJECT_ROOT / "output"

REPORT_DIR = OUTPUT_DIR / "Reports"

LOG_DIR = OUTPUT_DIR / "Logs"

TEMP_DIR = OUTPUT_DIR / "Temp"

CACHE_DIR = OUTPUT_DIR / "Cache"

CONFIG_DIR = PROJECT_ROOT / "config"
QUICK_FILTER_FILE = CONFIG_DIR / "quick_filters.json"