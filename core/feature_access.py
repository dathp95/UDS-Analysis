"""
Feature access policy for application tabs and licensed features.

This module is the central place for mapping features to license access.
It contains no UI code and no license file validation logic.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path


class Feature(str, Enum):
    CRC_CONVERTER = "crc_converter"
    LICENSE_SUPPORT = "license_support"
    LOG_ANALYZER = "log_analyzer"
    VEHICLE_MANAGER = "vehicle_manager"
    CODING_VALUE = "coding_value"
    CAN_INTERFACE = "can_interface"


FREE_FEATURES = frozenset({
    Feature.CRC_CONVERTER,
    Feature.LICENSE_SUPPORT,
})


def load_deactivated_features(config_file: Path) -> set[Feature]:
    """
    Read release-time disabled features from a JSON config file.
    """

    if not config_file.exists():
        return set()

    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()

    feature_values = data.get("deactivated_features", [])
    if not isinstance(feature_values, list):
        return set()

    deactivated_features = set()
    for value in feature_values:
        try:
            deactivated_features.add(Feature(value))
        except ValueError:
            continue

    return deactivated_features


def is_feature_enabled(
    feature: Feature,
    license_is_valid: bool,
    deactivated_features: set[Feature] | None = None,
) -> bool:
    """
    Return whether a feature is available for the current license state.
    """

    if deactivated_features and feature in deactivated_features:
        return False

    if license_is_valid:
        return True

    return feature in FREE_FEATURES
