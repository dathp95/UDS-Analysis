from __future__ import annotations

import base64
import binascii
import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from .exceptions import LicenseError
from .models import License
from .trusted_public_key import TRUSTED_PUBLIC_KEY_PEM

ACTIVATION_TOKEN_VERSION = 1
ACTIVATION_ALGORITHM = "RSA-PSS-SHA256"
MAX_ACTIVATION_TOKEN_LENGTH = 16_384
_B64URL_RE = re.compile(r"^[A-Za-z0-9_-]+$")

_REQUIRED_PAYLOAD_FIELDS = {
    "version",
    "license_id",
    "device_id",
    "customer",
    "edition",
    "issued_at",
    "expires_at",
}


class ActivationTokenError(LicenseError):
    default_message = "Invalid activation key."


@dataclass(frozen=True, slots=True)
class ActivationResult:
    success: bool
    license: License | None = None
    error_message: str = ""

    @classmethod
    def ok(cls, license_model: License) -> "ActivationResult":
        return cls(success=True, license=license_model, error_message="")

    @classmethod
    def failed(cls, error_message: str) -> "ActivationResult":
        return cls(success=False, license=None, error_message=error_message)


class ActivationStorage:

    def __init__(self, path: Path):
        self.path = path

    def read(self) -> str:
        if not self.path.is_file():
            raise ActivationTokenError(
                f"Activation file not found: {self.path}"
            )

        try:
            if self.path.stat().st_size > MAX_ACTIVATION_TOKEN_LENGTH:
                raise ActivationTokenError("Activation file is too large.")
            return self.path.read_text(encoding="utf-8").strip()
        except ActivationTokenError:
            raise
        except OSError as error:
            raise ActivationTokenError(
                f"Unable to read activation file: {error}"
            ) from error

    def save(self, activation_token: str) -> None:
        token = activation_token.strip()
        if len(token) > MAX_ACTIVATION_TOKEN_LENGTH:
            raise ActivationTokenError("Activation key is too large.")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_name(f"{self.path.name}.tmp")
        try:
            temp_path.write_text(token, encoding="utf-8")
            os.replace(temp_path, self.path)
        except OSError as error:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise ActivationTokenError(
                f"Unable to save activation file: {error}"
            ) from error


def create_activation_token(
    payload: dict[str, Any],
    private_key: RSAPrivateKey,
) -> str:
    payload_bytes = _canonical_payload_bytes(payload)
    signature = private_key.sign(
        payload_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return f"{_b64url_encode(payload_bytes)}.{_b64url_encode(signature)}"


def validate_activation_token(
    activation_token: str,
    *,
    expected_device_id: str,
    public_key: RSAPublicKey | None = None,
    now: datetime | None = None,
) -> License:
    payload_bytes, signature = _split_token(activation_token)
    public_key = public_key or load_trusted_public_key()
    _verify_signature(payload_bytes, signature, public_key)
    payload = _parse_payload(payload_bytes)
    _validate_payload_schema(payload)

    issued_at = _parse_utc_datetime(payload["issued_at"], "issued_at")
    expires_at = _parse_utc_datetime(payload["expires_at"], "expires_at")
    if issued_at >= expires_at:
        raise ActivationTokenError("Activation issued_at must be before expires_at.")

    current_time = _normalize_now(now)
    if issued_at > current_time:
        raise ActivationTokenError("Activation key is not valid yet.")

    if expires_at <= current_time:
        raise ActivationTokenError("Activation key has expired.")

    if payload["device_id"] != expected_device_id:
        raise ActivationTokenError("Activation key does not match this device.")

    return License(
        customer=payload["customer"].strip(),
        edition=payload["edition"].strip(),
        issue_date=issued_at,
        expire_date=expires_at,
        metadata={
            "license_id": payload["license_id"],
            "device_id": payload["device_id"],
            "activation_version": payload["version"],
            "activation_algorithm": ACTIVATION_ALGORITHM,
        },
    )


def load_trusted_public_key() -> RSAPublicKey:
    return load_public_key_from_pem(TRUSTED_PUBLIC_KEY_PEM)


def load_public_key_from_pem(pem_data: bytes) -> RSAPublicKey:
    try:
        key = serialization.load_pem_public_key(pem_data)
    except Exception as error:
        raise ActivationTokenError("Trusted public key is invalid.") from error

    if not isinstance(key, RSAPublicKey):
        raise ActivationTokenError("Trusted public key is not an RSA key.")

    return key


def _canonical_payload_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _split_token(activation_token: str) -> tuple[bytes, bytes]:
    if not isinstance(activation_token, str):
        raise ActivationTokenError("Activation key must be text.")

    token = activation_token.strip()
    if not token or len(token) > MAX_ACTIVATION_TOKEN_LENGTH:
        raise ActivationTokenError("Malformed activation key.")

    parts = token.split(".")
    if len(parts) != 2 or not all(parts):
        raise ActivationTokenError("Malformed activation key.")

    return _b64url_decode(parts[0]), _b64url_decode(parts[1])


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    if "=" in value or _B64URL_RE.fullmatch(value) is None:
        raise ActivationTokenError("Invalid activation key encoding.")

    padding_needed = (-len(value)) % 4
    padded = value + ("=" * padding_needed)
    try:
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
    except (binascii.Error, ValueError, UnicodeEncodeError) as error:
        raise ActivationTokenError("Invalid activation key encoding.") from error

    if _b64url_encode(decoded) != value:
        raise ActivationTokenError("Invalid activation key encoding.")

    return decoded


def _verify_signature(
    payload_bytes: bytes,
    signature: bytes,
    public_key: RSAPublicKey,
) -> None:
    try:
        public_key.verify(
            signature,
            payload_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
    except InvalidSignature as error:
        raise ActivationTokenError("Activation signature verification failed.") from error


def _parse_payload(payload_bytes: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ActivationTokenError("Activation payload is invalid.") from error

    if not isinstance(payload, dict):
        raise ActivationTokenError("Activation payload must be an object.")

    return payload


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    missing_fields = _REQUIRED_PAYLOAD_FIELDS - payload.keys()
    if missing_fields:
        raise ActivationTokenError(
            f"Activation payload missing field(s): {', '.join(sorted(missing_fields))}"
        )

    extra_fields = payload.keys() - _REQUIRED_PAYLOAD_FIELDS
    if extra_fields:
        raise ActivationTokenError(
            f"Activation payload has unsupported field(s): {', '.join(sorted(extra_fields))}"
        )

    if payload["version"] != ACTIVATION_TOKEN_VERSION:
        raise ActivationTokenError(
            f"Unsupported activation version: {payload['version']}"
        )

    for field_name in (
        "license_id",
        "device_id",
        "customer",
        "edition",
        "issued_at",
        "expires_at",
    ):
        value = payload[field_name]
        if not isinstance(value, str) or not value.strip():
            raise ActivationTokenError(
                f"Activation payload field {field_name} must be non-empty text."
            )


def _parse_utc_datetime(value: str, field_name: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ActivationTokenError(
            f"Activation payload field {field_name} must be an ISO datetime."
        ) from error

    if parsed.tzinfo is None:
        raise ActivationTokenError(
            f"Activation payload field {field_name} must include timezone."
        )

    return parsed.astimezone(UTC)


def _normalize_now(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(UTC)

    if now.tzinfo is None:
        raise ActivationTokenError("Current time must be timezone-aware.")

    return now.astimezone(UTC)
