"""
license/manager.py

Public API for the License System.

This is the ONLY module that should be used
outside the license package.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .activation import (
    ActivationResult,
    ActivationStorage,
    validate_activation_token,
)
from .device_identity import DeviceIdentity
from .exceptions import LicenseError
from .models import License
from .paths import (
    ACTIVATION_FILE_PATH,
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
        Read and validate the current machine-bound activation.

        Returns
        -------
        License
            Validated license object.

        Raises
        ------
        LicenseError
            If the license is invalid.
        """

        logger.debug("Starting activation validation.")

        active_device_id = LicenseManager.get_device_id()
        activation_token = ActivationStorage(ACTIVATION_FILE_PATH).read()

        license_model = validate_activation_token(
            activation_token,
            expected_device_id=active_device_id,
        )

        logger.info(
            "Activation validated successfully: %s (%s)",
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

    @staticmethod
    def get_device_id() -> str:
        return DeviceIdentity().get_device_id()

    @staticmethod
    def activate(activation_key: str) -> ActivationResult:
        try:
            active_device_id = LicenseManager.get_device_id()
            license_model = validate_activation_token(
                activation_key,
                expected_device_id=active_device_id,
            )
            ActivationStorage(ACTIVATION_FILE_PATH).save(activation_key)
        except LicenseError as error:
            logger.info("Activation failed: %s", error)
            return ActivationResult.failed(str(error))

        logger.info(
            "Activation saved successfully: %s (%s)",
            license_model.customer,
            license_model.edition,
        )
        return ActivationResult.ok(license_model)
