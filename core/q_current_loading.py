from dataclasses import dataclass
from datetime import datetime
from time import perf_counter

from core.q_current_analysis import parse_q_current_timestamp


@dataclass(frozen=True)
class QCurrentWorkspaceData:
    samples: list
    elapsed_seconds: list[float] | None
    time_bounds: tuple[float, float] | None
    timestamp_error: str | None = None


def calculate_elapsed_seconds(samples):
    parsed_values = [parse_q_current_timestamp(sample.time) for sample in samples]
    if not parsed_values:
        return []
    first_value = parsed_values[0]
    elapsed_seconds = []
    for parsed_value in parsed_values:
        if isinstance(first_value, datetime) and isinstance(parsed_value, datetime):
            elapsed_seconds.append((parsed_value - first_value).total_seconds())
        elif not isinstance(first_value, datetime) and not isinstance(parsed_value, datetime):
            elapsed_seconds.append(float(parsed_value) - float(first_value))
        else:
            raise ValueError("Current data contains mixed timestamp formats")
    return elapsed_seconds


def prepare_workspace_data(samples):
    samples = samples if isinstance(samples, list) else list(samples)
    try:
        elapsed = calculate_elapsed_seconds(samples)
    except ValueError as error:
        return QCurrentWorkspaceData(samples, None, None, str(error))
    bounds = (float(min(elapsed)), float(max(elapsed))) if elapsed else None
    return QCurrentWorkspaceData(samples, elapsed, bounds)


def timed_call(timings, name, callback, *args, **kwargs):
    start = perf_counter()
    try:
        return callback(*args, **kwargs)
    finally:
        timings[name] = perf_counter() - start
