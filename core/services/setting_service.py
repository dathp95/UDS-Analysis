"""
    Responsibilities:

        fn_load_settings()

        fn_save_settings()

        fn_get_last_export_folder()

        fn_set_last_export_folder()

    This service will be reusable later for:

        Theme
        Window size
        Recent files
        Language
        ECU configuration
"""

import json

from pathlib import Path
from config.paths import CONFIG_DIR


class SettingsService:

    def __init__(self):

        self.settings_file = Path(
            CONFIG_DIR / "settings.json"
        )

        self._settings = self._fn_load()

    # ==========================================
    # Private
    # ==========================================

    def _fn_load(self):

        if not self.settings_file.exists():

            return {}

        with open(
            self.settings_file,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    def _fn_save(self):

        with open(
            self.settings_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self._settings,
                file,
                indent=4
            )
        # ==========================================
    # Public API
    # ==========================================

    def fn_get(

        self,

        key,

        default=None

    ):

        return self._settings.get(

            key,

            default

        )

    def fn_set(

        self,

        key,

        value

    ):

        self._settings[key] = value

        self._fn_save()