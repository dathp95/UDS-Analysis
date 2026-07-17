"""

Validate a license.

Responsibilities
----------------
- Verify RSA signature
- Parse payload JSON
- Create License model
- Validate expiration date

This module MUST NOT:
- Read license file
- Show UI
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .crypto import load_public_key, verify_signature
from .exceptions import (
    LicenseExpiredError,
    LicenseInvalidError,
    LicenseParseError,
)
from .loader import RawLicense
from .models import License

logger = logging.getLogger(__name__)


def validate_license(
    raw_license: RawLicense,
    public_key_path: Path,
) -> License:
    """
    Validate a raw license.

    Parameters
    ----------
    raw_license
        Raw license loaded from loader.py

    public_key_path
        Path to public.pem

    Returns
    -------
    License

    Raises
    ------
    LicenseInvalidError
    LicenseExpiredError
    LicenseParseError
    """

    logger.debug("Validating license...")

    public_key = load_public_key(public_key_path)

    _verify_signature(
        raw_license=raw_license,
        public_key=public_key,
    )

    payload = _parse_payload(
        raw_license.payload,
    )

    license_model = License.from_dict(payload)

    _validate_expiration(
        license_model,
    )

    logger.debug(
        "License validation successful."
    )

    return license_model


def _verify_signature(
    raw_license: RawLicense,
    public_key,
) -> None:
    """
    Verify RSA signature.
    """

    is_valid = verify_signature(
        payload=raw_license.payload,
        signature=raw_license.signature,
        public_key=public_key,
    )

    if not is_valid:
        raise LicenseInvalidError(
            "License signature verification failed."
        )

    logger.debug("Signature verified.")


def _parse_payload(
    payload: bytes,
) -> dict[str, Any]:
    """
    Parse payload JSON.
    """

    try:
        return json.loads(
            payload.decode("utf-8")
        )

    except UnicodeDecodeError as ex:
        raise LicenseParseError(
            "Payload is not UTF-8."
        ) from ex

    except json.JSONDecodeError as ex:
        raise LicenseParseError(
            "Payload is not valid JSON."
        ) from ex


def _validate_expiration(
    license_model: License,
) -> None:
    """
    Validate license expiration.
    """

    if license_model.is_expired:
        raise LicenseExpiredError(
            f"License expired on "
            f"{license_model.expire_date.strftime('%d/%m/%Y %H:%M:%S')}."
        )

    logger.debug(
        "License valid until %s (%d day(s) remaining).",
        license_model.expire_date.strftime("%d/%m/%Y %H:%M:%S"),
        license_model.days_remaining,
    )