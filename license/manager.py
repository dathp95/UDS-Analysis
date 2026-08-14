"""
license/manager.py

Public API for the License System.

This is the ONLY module that should be used
outside the license package.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .exceptions import LicenseError
from .models import License
from .paths import (
    LICENSE_FILE_PATH,
    PUBLIC_KEY_PATH,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LicenseStatus:
    """
    Result of license validation for application startup/access control.
    """

    is_valid: bool
    license: License | None = None
    error_message: str = ""

    @classmethod
    def valid(cls, license: License | None = None) -> "LicenseStatus":
        return cls(
            is_valid=True,
            license=license,
            error_message="",
        )

    @classmethod
    def invalid(cls, error_message: str = "") -> "LicenseStatus":
        return cls(
            is_valid=False,
            license=None,
            error_message=error_message,
        )


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

        from .loader import read_license
        from .validator import validate_license

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
    def get_status() -> LicenseStatus:
        """
        Return current license status without raising validation errors.
        """

        try:
            license_model = LicenseManager.validate()
            return LicenseStatus.valid(license_model)

        except LicenseError as error:
            logger.info(
                "License validation failed: %s",
                error,
            )
            return LicenseStatus.invalid(str(error))

    @staticmethod
    def is_valid() -> bool:
        """
        Check whether the current license is valid.

        Returns
        -------
        bool
            True if the license is valid, otherwise False.
        """

        return LicenseManager.get_status().is_valid
