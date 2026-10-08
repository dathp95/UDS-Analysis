"""
Machine-bound Device ID provider.

Windows MachineGuid is used when available, but the raw value is never exposed.
The Device ID is a SHA-256-derived fingerprint for license binding, not
tamper-proof hardware attestation.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable

from .exceptions import LicenseError


class DeviceIdentityError(LicenseError):
    default_message = "Unable to determine device identity."


class DeviceIdentity:

    DEVICE_ID_PREFIX = "VC"

    def __init__(self, identifier_provider: Callable[[], str] | None = None):
        self._identifier_provider = identifier_provider or self._default_identifier

    def get_device_id(self) -> str:
        raw_identifier = self._identifier_provider()
        normalized = self._normalize_identifier(raw_identifier)
        if not normalized:
            raise DeviceIdentityError()

        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper()
        groups = [
            digest[index:index + 4]
            for index in range(0, 20, 4)
        ]
        return f"{self.DEVICE_ID_PREFIX}-" + "-".join(groups)

    @classmethod
    def _normalize_identifier(cls, value: str | None) -> str:
        if value is None:
            return ""

        value = value.strip().strip("{}").upper()
        return re.sub(r"[^A-Z0-9-]", "", value)

    def _default_identifier(self) -> str:
        machine_guid = self._windows_machine_guid()
        if machine_guid:
            return f"WINDOWS-MACHINEGUID:{machine_guid}"

        return ""

    @staticmethod
    def _windows_machine_guid() -> str:
        try:
            import winreg
        except ImportError:
            return ""

        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
            ) as registry_key:
                value, _value_type = winreg.QueryValueEx(
                    registry_key,
                    "MachineGuid",
                )
        except OSError:
            return ""

        return str(value).strip()
