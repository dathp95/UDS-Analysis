"""
license/loader.py

Read and parse a license file.

Responsibilities
----------------
- Read license file
- Parse JSON
- Validate license structure
- Decode Base64 payload/signature

This module MUST NOT:
- Verify RSA signature
- Validate expiration
- Create License model
- Show UI
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .exceptions import (
    LicenseFormatError,
    LicenseNotFoundError,
    LicenseParseError,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

LICENSE_VERSION = 1
LICENSE_ALGORITHM = "RSA-PSS-SHA256"

_REQUIRED_FIELDS = frozenset(
    {
        "version",
        "algorithm",
        "payload",
        "signature",
    }
)


# ============================================================================
# Data Model
# ============================================================================

@dataclass(slots=True)
class RawLicense:
    """
    Raw license data after reading the license file.

    Attributes
    ----------
    payload
        Original payload bytes.

    signature
        RSA signature bytes.
    """

    payload: bytes
    signature: bytes


# ============================================================================
# Public API
# ============================================================================

def read_license(license_path: Path) -> RawLicense:
    """
    Read and decode a license file.

    Parameters
    ----------
    license_path
        Path to license.lic

    Returns
    -------
    RawLicense

    Raises
    ------
    LicenseNotFoundError
    LicenseParseError
    LicenseFormatError
    """

    logger.debug("Loading license: %s", license_path)

    if not license_path.is_file():
        raise LicenseNotFoundError(
            f"License file not found: {license_path}"
        )

    try:
        content = license_path.read_text(encoding="utf-8")
    except OSError as ex:
        raise LicenseParseError(
            f"Unable to read license file: {ex}"
        ) from ex

    data = _parse_json(content)

    _validate_structure(data)

    logger.debug("License file loaded successfully.")

    return RawLicense(
        payload=_decode_base64(data["payload"]),
        signature=_decode_base64(data["signature"]),
    )


# ============================================================================
# Private Helpers
# ============================================================================

def _parse_json(content: str) -> dict[str, Any]:
    """
    Parse JSON string.
    """

    try:
        return json.loads(content)

    except json.JSONDecodeError as ex:
        raise LicenseParseError(
            f"Invalid JSON format: {ex}"
        ) from ex


def _decode_base64(value: str) -> bytes:
    """
    Decode Base64 string into bytes.
    """

    try:
        return base64.b64decode(value, validate=True)

    except (binascii.Error, ValueError) as ex:
        raise LicenseParseError(
            "Invalid Base64 encoded data."
        ) from ex


def _validate_structure(data: dict[str, Any]) -> None:
    """
    Validate license structure.
    """

    missing_fields = _REQUIRED_FIELDS - data.keys()

    if missing_fields:
        raise LicenseFormatError(
            f"Missing required field(s): "
            f"{', '.join(sorted(missing_fields))}"
        )

    if data["version"] != LICENSE_VERSION:
        raise LicenseFormatError(
            f"Unsupported license version: "
            f"{data['version']}"
        )

    if data["algorithm"] != LICENSE_ALGORITHM:
        raise LicenseFormatError(
            f"Unsupported algorithm: "
            f"{data['algorithm']}"
        )

    if not isinstance(data["payload"], str):
        raise LicenseFormatError(
            "payload must be a Base64 string."
        )

    if not isinstance(data["signature"], str):
        raise LicenseFormatError(
            "signature must be a Base64 string."
        )