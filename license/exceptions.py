"""
license/exceptions.py

Custom exceptions for the License System.

All license-related errors should inherit from LicenseError.
"""


class LicenseError(Exception):
    """
    Base exception for all license errors.
    """

    default_message = "Unknown license error."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default_message)


class LicenseNotFoundError(LicenseError):
    """
    Raised when the license file cannot be found.
    """

    default_message = "License file not found."


class LicenseInvalidError(LicenseError):
    """
    Raised when the license signature is invalid.
    """

    default_message = "Invalid license signature."


class LicenseExpiredError(LicenseError):
    """
    Raised when the license has expired.
    """

    default_message = "License has expired."


class LicenseParseError(LicenseError):
    """
    Raised when the license file cannot be parsed.
    """

    default_message = "Failed to parse license file."


class LicenseFormatError(LicenseError):
    """
    Raised when the license structure is invalid.
    """

    default_message = "Invalid license format."


class PublicKeyError(LicenseError):
    """
    Raised when the public key is missing or invalid.
    """

    default_message = "Public key is invalid."