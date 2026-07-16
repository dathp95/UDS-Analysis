"""
license/crypto.py

RSA cryptographic utilities for the License System.

Responsibilities
----------------
- Load RSA public key
- Verify RSA signature

This module MUST NOT:
- Read license files
- Parse JSON
- Validate expiration
- Show UI
"""

from __future__ import annotations

from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key

from .exceptions import PublicKeyError


def load_public_key(public_key_path: Path) -> RSAPublicKey:
    """
    Load RSA public key from a PEM file.

    Parameters
    ----------
    public_key_path : Path
        Path to public.pem

    Returns
    -------
    RSAPublicKey

    Raises
    ------
    PublicKeyError
        If the file is missing or invalid.
    """

    try:
        pem_data = public_key_path.read_bytes()

    except FileNotFoundError as ex:
        raise PublicKeyError(
            f"Public key not found: {public_key_path}"
        ) from ex

    except Exception as ex:
        raise PublicKeyError(
            f"Unable to read public key: {ex}"
        ) from ex

    try:
        key = load_pem_public_key(pem_data)

        if not isinstance(key, RSAPublicKey):
            raise PublicKeyError(
                "The loaded key is not an RSA public key."
            )

        return key

    except Exception as ex:
        raise PublicKeyError(
            f"Invalid public key: {ex}"
        ) from ex


def verify_signature(
    payload: bytes,
    signature: bytes,
    public_key: RSAPublicKey,
) -> bool:
    """
    Verify RSA signature.

    Parameters
    ----------
    payload : bytes
        Original payload.

    signature : bytes
        RSA signature.

    public_key : RSAPublicKey
        Loaded public key.

    Returns
    -------
    bool
        True if signature is valid,
        otherwise False.
    """

    try:

        public_key.verify(
            signature,
            payload,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )

        return True

    except InvalidSignature:
        return False


