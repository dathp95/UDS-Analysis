from config.paths import (
    OUTPUT_DIR,
    REPORT_DIR,
    LOG_DIR,
    TEMP_DIR,
    CACHE_DIR,
)


def ensure_directories():
    """Create required application directories if they don't exist."""

    for folder in (
        OUTPUT_DIR,
        REPORT_DIR,
        LOG_DIR,
        TEMP_DIR,
        CACHE_DIR,
    ):
        folder.mkdir(parents=True, exist_ok=True)