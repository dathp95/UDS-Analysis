from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from config.paths import Q_CURRENT_CONFIG_FILE


CONFIG_VERSION = 1
MAX_CURRENT_MA = 1_000_000.0
MAX_WAKE_DURATION_S = 3600.0
MIN_SAMPLING_DURATION_MIN = 5.0
MAX_SAMPLING_DURATION_MIN = 1440.0
DEFAULT_SAMPLING_DURATION_MIN = 60.0


@dataclass(frozen=True)
class QCurrentConfig:
    standard_current_ma: float
    wake_up_limit_ma: float
    wake_duration_s: float
    sampling_duration_enabled: bool = True
    sampling_duration_min: float = DEFAULT_SAMPLING_DURATION_MIN


DEFAULT_Q_CURRENT_CONFIG = QCurrentConfig(
    standard_current_ma=30.0,
    wake_up_limit_ma=300.0,
    wake_duration_s=2.0,
    sampling_duration_enabled=True,
    sampling_duration_min=DEFAULT_SAMPLING_DURATION_MIN,
)


def load_q_current_config(config_file: str | Path | None = None) -> QCurrentConfig:
    path = _resolve_config_file(config_file)
    if not path.exists():
        return DEFAULT_Q_CURRENT_CONFIG
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return DEFAULT_Q_CURRENT_CONFIG
        sampling_duration_enabled, sampling_duration_min = _read_sampling_duration(data)
        config = QCurrentConfig(
            standard_current_ma=_read_number(data, "standard_current_ma"),
            wake_up_limit_ma=_read_number(data, "wake_up_limit_ma"),
            wake_duration_s=_read_number(data, "wake_duration_s"),
            sampling_duration_enabled=sampling_duration_enabled,
            sampling_duration_min=sampling_duration_min,
        )
        validate_q_current_config(config)
        return config
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return DEFAULT_Q_CURRENT_CONFIG


def save_q_current_config(
    config: QCurrentConfig,
    config_file: str | Path | None = None,
) -> None:
    validate_q_current_config(config)
    path = _resolve_config_file(config_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    payload = {
        "version": CONFIG_VERSION,
        "standard_current_ma": float(config.standard_current_ma),
        "wake_up_limit_ma": float(config.wake_up_limit_ma),
        "wake_duration_s": float(config.wake_duration_s),
        "sampling_duration_enabled": bool(config.sampling_duration_enabled),
        "sampling_duration_min": float(config.sampling_duration_min),
    }
    temporary_path.write_text(
        json.dumps(payload, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def validate_q_current_config(config: QCurrentConfig) -> None:
    standard_current_ma = _validate_number(
        config.standard_current_ma,
        "standard_current_ma",
    )
    wake_up_limit_ma = _validate_number(
        config.wake_up_limit_ma,
        "wake_up_limit_ma",
    )
    wake_duration_s = _validate_number(
        config.wake_duration_s,
        "wake_duration_s",
    )
    sampling_duration_min = _validate_number(
        config.sampling_duration_min,
        "sampling_duration_min",
    )
    if not isinstance(config.sampling_duration_enabled, bool):
        raise ValueError("sampling_duration_enabled must be a boolean")

    if not 0.0 <= standard_current_ma <= MAX_CURRENT_MA:
        raise ValueError("standard_current_ma must be between 0 and 1000000 mA")
    if not 0.0 <= wake_up_limit_ma <= MAX_CURRENT_MA:
        raise ValueError("wake_up_limit_ma must be between 0 and 1000000 mA")
    if wake_up_limit_ma < standard_current_ma:
        raise ValueError("wake_up_limit_ma must be greater than or equal to standard_current_ma")
    if not 0.0 < wake_duration_s <= MAX_WAKE_DURATION_S:
        raise ValueError("wake_duration_s must be greater than 0 and at most 3600 s")
    if not MIN_SAMPLING_DURATION_MIN <= sampling_duration_min <= MAX_SAMPLING_DURATION_MIN:
        raise ValueError("sampling_duration_min must be between 5 and 1440 min")


def _resolve_config_file(config_file: str | Path | None) -> Path:
    return Path(config_file) if config_file is not None else Q_CURRENT_CONFIG_FILE


def _read_number(data: dict, key: str) -> float:
    if key not in data:
        raise ValueError(f"Missing Q Current config field: {key}")
    return _validate_number(data[key], key)


def _read_sampling_duration(data: dict) -> tuple[bool, float]:
    try:
        enabled = data.get("sampling_duration_enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError("sampling_duration_enabled must be a boolean")
        duration_min = data.get(
            "sampling_duration_min",
            DEFAULT_SAMPLING_DURATION_MIN,
        )
        duration_min = _validate_number(duration_min, "sampling_duration_min")
        if not MIN_SAMPLING_DURATION_MIN <= duration_min <= MAX_SAMPLING_DURATION_MIN:
            raise ValueError("sampling_duration_min must be between 5 and 1440 min")
        return enabled, duration_min
    except (ValueError, TypeError):
        return True, DEFAULT_SAMPLING_DURATION_MIN


def _validate_number(value, key: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a finite number")
    numeric_value = float(value)
    if not math.isfinite(numeric_value):
        raise ValueError(f"{key} must be a finite number")
    return numeric_value