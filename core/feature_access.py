"""
Feature access policy for application tabs and licensed features.

This module is the central place for mapping features to license access.
It contains no UI code and no license file validation logic.
"""

from __future__ import annotations

from enum import Enum


class Feature(str, Enum):
    CRC_CONVERTER = "crc_converter"
    LICENSE_SUPPORT = "license_support"
    LOG_ANALYZER = "log_analyzer"
    VEHICLE_MANAGER = "vehicle_manager"
    CODING_VALUE = "coding_value"


FREE_FEATURES = frozenset({
    Feature.CRC_CONVERTER,
    Feature.LICENSE_SUPPORT,
})


def is_feature_enabled(
    feature: Feature,
    license_is_valid: bool,
) -> bool:
    """
    Return whether a feature is available for the current license state.
    """

    if license_is_valid:
        return True

    return feature in FREE_FEATURES
