from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import median
from typing import Iterable


class CurrentClassification(Enum):
    NORMAL_SLEEP = "NORMAL_SLEEP"
    WAKE_UP_CANDIDATE = "WAKE_UP_CANDIDATE"
    EXCLUDED = "EXCLUDED"


@dataclass(frozen=True)
class QCurrentWakeUpInterval:
    start_s: float
    end_s: float
    duration_s: float
    peak_current_ma: float


@dataclass(frozen=True)
class QCurrentAnalysisResult:
    result_status: str
    average_sleep_current_ma: float | None
    minimum_sleep_current_ma: float | None
    maximum_sleep_current_ma: float | None
    wake_up_event_count: int
    total_wake_up_duration_s: float
    average_wake_up_duration_s: float | None
    maximum_wake_up_duration_s: float | None
    average_wake_up_interval_s: float | None
    minimum_wake_up_interval_s: float | None
    maximum_wake_up_interval_s: float | None
    longest_continuous_sleep_s: float | None
    start_time_s: float | None
    end_time_s: float | None
    duration_s: float | None
    total_samples: int
    sample_interval_s: float | None
    wake_up_intervals: tuple[QCurrentWakeUpInterval, ...]


def classify_current(
    current_ma: float,
    standard_current_ma: float,
    wake_up_limit_ma: float,
) -> CurrentClassification:
    magnitude = abs(float(current_ma))
    standard_current_ma = abs(float(standard_current_ma))
    wake_up_limit_ma = abs(float(wake_up_limit_ma))

    if magnitude <= standard_current_ma:
        return CurrentClassification.NORMAL_SLEEP
    if magnitude <= wake_up_limit_ma:
        return CurrentClassification.WAKE_UP_CANDIDATE
    return CurrentClassification.EXCLUDED


def analyze_q_current(
    time_seconds: Iterable[float],
    current_ma: Iterable[float],
    standard_current_ma: float,
    wake_up_limit_ma: float,
    wake_duration_s: float,
) -> QCurrentAnalysisResult:
    pairs = sorted(
        (float(time_s), float(current))
        for time_s, current in zip(time_seconds, current_ma)
    )
    if not pairs:
        return _empty_result()

    times = [pair[0] for pair in pairs]
    currents = [pair[1] for pair in pairs]
    magnitudes = [abs(current) for current in currents]
    standard_current_ma = abs(float(standard_current_ma))
    wake_up_limit_ma = abs(float(wake_up_limit_ma))
    wake_duration_s = max(0.0, float(wake_duration_s))

    included_indexes = [
        index
        for index, magnitude in enumerate(magnitudes)
        if magnitude <= wake_up_limit_ma
    ]
    included_magnitudes = [magnitudes[index] for index in included_indexes]

    wake_up_intervals, wake_indexes = _detect_wake_up_intervals(
        times,
        magnitudes,
        standard_current_ma,
        wake_up_limit_ma,
        wake_duration_s,
    )

    average_sleep_current = _mean(included_magnitudes)
    result_status = (
        "PASSED"
        if average_sleep_current is not None
        and average_sleep_current <= standard_current_ma
        else "FAILED"
    )

    wake_durations = [interval.duration_s for interval in wake_up_intervals]
    wake_gaps = [
        wake_up_intervals[index].start_s - wake_up_intervals[index - 1].end_s
        for index in range(1, len(wake_up_intervals))
    ]

    deltas = [
        times[index] - times[index - 1]
        for index in range(1, len(times))
    ]

    return QCurrentAnalysisResult(
        result_status=result_status,
        average_sleep_current_ma=average_sleep_current,
        minimum_sleep_current_ma=(
            min(included_magnitudes) if included_magnitudes else None
        ),
        maximum_sleep_current_ma=(
            max(included_magnitudes) if included_magnitudes else None
        ),
        wake_up_event_count=len(wake_up_intervals),
        total_wake_up_duration_s=sum(wake_durations),
        average_wake_up_duration_s=_mean(wake_durations),
        maximum_wake_up_duration_s=max(wake_durations) if wake_durations else None,
        average_wake_up_interval_s=_mean(wake_gaps),
        minimum_wake_up_interval_s=min(wake_gaps) if wake_gaps else None,
        maximum_wake_up_interval_s=max(wake_gaps) if wake_gaps else None,
        longest_continuous_sleep_s=_longest_continuous_sleep_duration(
            times,
            included_indexes,
            wake_indexes,
        ),
        start_time_s=times[0],
        end_time_s=times[-1],
        duration_s=times[-1] - times[0],
        total_samples=len(times),
        sample_interval_s=median(deltas) if deltas else None,
        wake_up_intervals=tuple(wake_up_intervals),
    )


def _detect_wake_up_intervals(
    times: list[float],
    magnitudes: list[float],
    standard_current_ma: float,
    wake_up_limit_ma: float,
    wake_duration_s: float,
) -> tuple[list[QCurrentWakeUpInterval], set[int]]:
    intervals = []
    wake_indexes = set()
    start_index = None

    for index, magnitude in enumerate(magnitudes):
        is_candidate = standard_current_ma < magnitude <= wake_up_limit_ma
        if is_candidate and start_index is None:
            start_index = index
        elif not is_candidate and start_index is not None:
            _append_wake_up_interval(
                intervals,
                wake_indexes,
                times,
                magnitudes,
                start_index,
                index - 1,
                wake_duration_s,
            )
            start_index = None

    if start_index is not None:
        _append_wake_up_interval(
            intervals,
            wake_indexes,
            times,
            magnitudes,
            start_index,
            len(times) - 1,
            wake_duration_s,
        )

    return intervals, wake_indexes


def _append_wake_up_interval(
    intervals: list[QCurrentWakeUpInterval],
    wake_indexes: set[int],
    times: list[float],
    magnitudes: list[float],
    start_index: int,
    end_index: int,
    min_duration_s: float,
) -> None:
    start_s = times[start_index]
    end_s = times[end_index]
    duration_s = end_s - start_s
    if duration_s < min_duration_s:
        return

    intervals.append(
        QCurrentWakeUpInterval(
            start_s=start_s,
            end_s=end_s,
            duration_s=duration_s,
            peak_current_ma=max(magnitudes[start_index : end_index + 1]),
        )
    )
    wake_indexes.update(range(start_index, end_index + 1))


def _longest_continuous_sleep_duration(
    times: list[float],
    included_indexes: list[int],
    wake_indexes: set[int],
) -> float | None:
    sleep_indexes = set(included_indexes) - wake_indexes
    if not sleep_indexes:
        return None

    longest = 0.0
    run_start = None
    previous_index = None

    for index in range(len(times)):
        if index not in sleep_indexes:
            if run_start is not None and previous_index is not None:
                longest = max(longest, times[previous_index] - times[run_start])
            run_start = None
            previous_index = None
            continue

        if run_start is None:
            run_start = index
        previous_index = index

    if run_start is not None and previous_index is not None:
        longest = max(longest, times[previous_index] - times[run_start])

    return longest


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _empty_result() -> QCurrentAnalysisResult:
    return QCurrentAnalysisResult(
        result_status="FAILED",
        average_sleep_current_ma=None,
        minimum_sleep_current_ma=None,
        maximum_sleep_current_ma=None,
        wake_up_event_count=0,
        total_wake_up_duration_s=0.0,
        average_wake_up_duration_s=None,
        maximum_wake_up_duration_s=None,
        average_wake_up_interval_s=None,
        minimum_wake_up_interval_s=None,
        maximum_wake_up_interval_s=None,
        longest_continuous_sleep_s=None,
        start_time_s=None,
        end_time_s=None,
        duration_s=None,
        total_samples=0,
        sample_interval_s=None,
        wake_up_intervals=(),
    )
