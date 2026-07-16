"""
license/manager.py

Public API for the License System.

This is the ONLY module that should be used
outside the license package.
"""

from __future__ import annotations

import logging

from .exceptions import LicenseError
from .loader import read_license
from .models import License
from .paths import (
    LICENSE_FILE_PATH,
    PUBLIC_KEY_PATH,
)
from .validator import validate_license

logger = logging.getLogger(__name__)


class LicenseManager:
    """
    Public interface for the License System.
    """

    @staticmethod
    def validate() -> License:
        """
        Read and validate the current license.

        Returns
        -------
        License
            Validated license object.

        Raises
        ------
        LicenseError
            If the license is invalid.
        """

        logger.debug("Starting license validation.")

        raw_license = read_license(
            LICENSE_FILE_PATH
        )

        license_model = validate_license(
            raw_license=raw_license,
            public_key_path=PUBLIC_KEY_PATH,
        )

        logger.info(
            "License validated successfully: %s (%s)",
            license_model.customer,
            license_model.edition,
        )

        return license_model

    @staticmethod
    def is_valid() -> bool:
        """
        Check whether the current license is valid.

        Returns
        -------
        bool
            True if the license is valid, otherwise False.
        """

        try:
            LicenseManager.validate()
            return True

        except LicenseError:
            logger.exception(
                "License validation failed."
            )
            return False