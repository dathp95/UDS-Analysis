import json
import os
import re
import tempfile
from pathlib import Path

from config.paths import (
    CONFIG_DIR,
    DISPLAY_NAMES_FILE,
    UDS_SERVICES_FILE,
    UDS_USER_FILE,
)


MAX_DISPLAY_NAMES_FILE_SIZE = 10 * 1024 * 1024

def load_uds_config(
    services_path=UDS_SERVICES_FILE,
    user_path=UDS_USER_FILE,
    legacy_path=CONFIG_DIR / "uds_config.json",
):

    if Path(services_path).is_file() and Path(user_path).is_file():
        return _load_uds_schema_v2(services_path, user_path)

    with open(legacy_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_uds_schema_v2(services_path, user_path):
    services_config = _load_json_object(services_path, "UDS services config")
    user_config = _load_json_object(user_path, "UDS user config")

    if services_config.get("schema_version") != 2:
        raise ValueError("UDS services config must use schema_version 2.")

    if user_config.get("schema_version") != 2:
        raise ValueError("UDS user config must use schema_version 2.")

    services = services_config.get("services")
    if not isinstance(services, dict) or not services:
        raise ValueError("UDS services config must contain services.")

    normalized_services = {}
    positive_sid = {}
    match_rule = {}

    for sid, definition in services.items():
        if not isinstance(definition, dict):
            raise ValueError(f"Service '{sid}' must be an object.")

        name = definition.get("name")
        positive = definition.get("positive_sid")
        match = definition.get("match", "none")

        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Service '{sid}' has an invalid name.")
        if not isinstance(positive, str):
            raise ValueError(f"Service '{sid}' has an invalid positive_sid.")
        if match not in {"did", "sub", "routine", "none"}:
            raise ValueError(f"Service '{sid}' has an invalid match rule.")

        normalized_sid = sid.upper().strip()
        normalized_services[normalized_sid] = name.strip()
        positive_sid[normalized_sid] = positive.upper().strip()
        match_rule[normalized_sid] = match

    timeout = services_config.get("timeout", {})
    if not isinstance(timeout, dict):
        raise ValueError("UDS services timeout must be an object.")

    positive_timeout = timeout.get("positive_response", 10.0)
    try:
        positive_timeout = float(positive_timeout)
    except (TypeError, ValueError) as error:
        raise ValueError("positive_response timeout must be numeric.") from error

    nrc = user_config.get("nrc", {})
    if not isinstance(nrc, dict):
        raise ValueError("UDS user config nrc must be an object.")

    return {
        "schema_version": 2,
        "timeout": {"positive_response": positive_timeout},
        "services": normalized_services,
        "positive_sid": positive_sid,
        "match_rule": match_rule,
        "nrc": {
            str(code).upper().strip(): str(name).strip()
            for code, name in nrc.items()
        },
        "dids": {},
        "routine_ids": {},
    }


def _load_json_object(path, label):
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid {label} JSON: {error.msg}.") from error

    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object.")

    return data

def load_display_names(path=DISPLAY_NAMES_FILE):

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def import_display_names(
    source_path,
    destination_path=DISPLAY_NAMES_FILE,
):
    """Validate and atomically copy a display-names JSON mapping."""

    source_path = Path(source_path)
    destination_path = Path(destination_path)

    if not source_path.is_file():
        raise FileNotFoundError("The selected display names file could not be found.")

    if source_path.stat().st_size > MAX_DISPLAY_NAMES_FILE_SIZE:
        raise ValueError("Display names file is too large (maximum is 10 MB).")

    try:
        with open(source_path, encoding="utf-8-sig") as f:
            data = json.load(f)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid display names JSON: {error.msg}.") from error

    _validate_display_names(data)

    if destination_path.exists() and destination_path.stat().st_size > 0:
        current = load_display_names(destination_path)
        if current:
            _validate_display_names(current)
    else:
        current = {}

    merged = {
        **current,
        **data,
    }
    _write_display_names(merged, destination_path)

    return merged


def import_display_name_rules(
    rules_text,
    destination_path=DISPLAY_NAMES_FILE,
):
    """Merge pipe-delimited display-name rules into the JSON mapping."""

    destination_path = Path(destination_path)
    if destination_path.exists() and destination_path.stat().st_size > 0:
        current = load_display_names(destination_path)
        if current:
            _validate_display_names(current)
    else:
        current = {}

    if len(rules_text.encode("utf-8")) > MAX_DISPLAY_NAMES_FILE_SIZE:
        raise ValueError("Display-name rules are too large (maximum is 10 MB).")

    normalized_current = {}
    for key, value in current.items():
        normalized_current[_normalize_rule_key(key)] = value

    imported_keys = set()
    rule_count = 0

    for line_number, raw_line in enumerate(rules_text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        rule_key, separator, display_name = line.partition("|")
        if not separator:
            raise ValueError(
                f"Line {line_number} must use format PAYLOAD|Display Name."
            )

        try:
            rule_key = _normalize_rule_key(rule_key)
        except ValueError as error:
            raise ValueError(f"Line {line_number}: {error}") from error

        display_name = " ".join(display_name.split())
        if not display_name:
            raise ValueError(f"Line {line_number} has an empty display name.")

        if rule_key in imported_keys:
            raise ValueError(f"Line {line_number} duplicates rule '{rule_key}'.")

        imported_keys.add(rule_key)
        current_value = normalized_current.get(rule_key, {})
        normalized_current[rule_key] = {
            **current_value,
            "display_name": display_name,
        }
        rule_count += 1

    if rule_count == 0:
        raise ValueError("Please enter at least one display-name rule.")

    _write_display_names(normalized_current, destination_path)
    return normalized_current


def _normalize_rule_key(value):
    tokens = re.split(r"\s+", value.strip().upper())

    if not 1 <= len(tokens) <= 8 or any(
        not re.fullmatch(r"[0-9A-F]{2}", token)
        for token in tokens
    ):
        raise ValueError(
            "Payload must contain 1 to 8 hexadecimal bytes, e.g. '22 F1 90'."
        )

    return " ".join(tokens)


def _write_display_names(data, destination_path):
    destination_path = Path(destination_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination_path.parent,
            prefix=f".{destination_path.stem}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump(data, temp_file, indent=4, ensure_ascii=False)
            temp_file.write("\n")

        os.replace(temp_path, destination_path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _validate_display_names(data):
    if not isinstance(data, dict) or not data:
        raise ValueError("Display names must be a non-empty JSON object.")

    for key, value in data.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("Display name keys must be non-empty strings.")

        if not isinstance(value, dict):
            raise ValueError(
                f"Display name '{key}' must be an object containing 'display_name'."
            )

        display_name = value.get("display_name")
        if not isinstance(display_name, str) or not display_name.strip():
            raise ValueError(
                f"Display name '{key}' must contain a non-empty 'display_name'."
            )
