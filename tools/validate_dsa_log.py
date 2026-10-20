"""Read-only local validation: python -m tools.validate_dsa_log [path] [--memory].

    Output is allowlisted aggregate data. No source path, device metadata,
    CAN IDs, raw frames, VINs, or private diagnostic payloads are printed.
"""

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import time
import tracemalloc

from core.asc_reader import get_log_channels, load_log
from core.ecu_mapping import load_vehicle_mapping
from core.log_parsers.diagnostics import ParserDiagnostics
from core.log_parsers.registry import detect_txt_parser
from core.pipeline import run_pipeline
from repositories.vehicle_repository import VehicleRepository


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = ROOT / "logs" / "RLLV8GKD4TH812470__20261020__083018__busdatalogger_can1.txt"
_CHECK_TIME = re.compile(r"\[([0-9]+):([0-9]+):([0-9]+)\.([0-9]+)\.([0-9]+)\]")
_CHECK_CHANNEL = re.compile(r"Ch([0-9]+)\s*\(CAN\)")
_CHECK_ID_DLC = re.compile(r"([0-9]+)\s+id:\s*0x([0-9a-fA-F]+)\s*$")
_CHECK_DIRECTION = re.compile(r"\bMsg\s+(T-{15}|-R-{14})")
_SERVICES = {
    "SessionControl 10 03": ("10 03", "50 03"),
    "ReadDID 22 F1 68": ("22 F1 68", "62 F1 68"),
    "SecurityAccess 27 03": ("27 03", "67 03"),
    "SecurityAccess 27 04": ("27 04", "67 04"),
    "RoutineControl 31 01 02 06": ("31 01 02 06", "71 01 02 06"),
}


def _fingerprint(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(65536), b""):
            digest.update(chunk)
    return digest.digest()


def _check_representative_records(path):
    parser = detect_txt_parser(path)
    compared = {"Tx": 0, "Rx": 0}
    directions = {"Tx": 0, "Rx": 0}
    matches = True
    with path.open(encoding="utf-8-sig") as source:
        for line in source:
            try:
                message = parser.parse_line(line)
            except ValueError:
                continue
            if message is None:
                continue
            direction = "Tx" if _CHECK_DIRECTION.search(line)[1].startswith("T") else "Rx"
            directions[direction] += 1
            if compared[direction] >= 10:
                continue
            before, _, after = line.partition(">")
            id_dlc = _CHECK_ID_DLC.search(before)
            timestamp = _CHECK_TIME.search(line)
            channel = _CHECK_CHANNEL.search(line)
            if not (id_dlc and timestamp and channel):
                matches = False
                continue
            hours, minutes, seconds, millis, micros = map(int, timestamp.groups())
            expected_time = ((hours * 3600 + minutes * 60 + seconds) * 1_000_000 + millis * 1000 + micros) / 1_000_000
            payload = bytes.fromhex(after.partition("<")[0])
            matches &= (int(id_dlc[2], 16) == message["can_id"]
                        and int(id_dlc[1]) == message["dlc"] == len(payload)
                        and int(channel[1]) == message["channel"]
                        and expected_time == message["timestamp"]
                        and payload == bytes(message["data"]))
            compared[direction] += 1
    return {"directions": directions, "representative_records_compared": sum(compared.values()),
            "representative_records_match_including_padding": matches}


def _has_prefix(payload, prefix):
    return payload == prefix or payload.startswith(prefix + " ")


def _uds_summary(path, channel, messages):
    observed_ids = {message["can_id"] for message in messages}
    repository = VehicleRepository()
    best_vehicle = None
    best_pairs = 0
    for name in repository.list_vehicles():
        try:
            vehicle = repository.load(name)
            mapping, _, _ = load_vehicle_mapping(vehicle)
        except (OSError, ValueError, KeyError, TypeError):
            continue
        pairs = sum(info["request"] in observed_ids and info["response"] in observed_ids for info in mapping.values())
        if pairs > best_pairs:
            best_vehicle, best_pairs = vehicle, pairs
    if best_vehicle is None:
        return {"status": "not_validated", "reason": "No existing vehicle configuration has matching request/response IDs."}
    result = run_pipeline(str(path), best_vehicle, channel=channel)
    transactions = result["transactions"]
    selected_mapping, _, _ = load_vehicle_mapping(best_vehicle)
    checks = {}
    for label, (request, response) in _SERVICES.items():
        matched = [tx for tx in transactions if _has_prefix(tx["request"]["payload"], request)]
        positive = [tx for tx in matched if tx["positive_response"]
                    and _has_prefix(tx["positive_response"]["payload"], response)]
        checks[label] = {
            "requests": len(matched), "positive_responses": len(positive),
            "response_pending_count": sum(tx["response_pending_count"] for tx in matched),
            "response_time_consistent": all(tx["response_time"] >= 0 and abs(tx["response_time"] -
                (tx["positive_response"]["timestamp"] - tx["request"]["timestamp"])) < 1e-9 for tx in positive) if positive else None,
            "can_id_association_consistent": all(
                tx["request"]["can_id"] == selected_mapping[tx["ecu"]]["request"]
                and all(nrc["can_id"] == selected_mapping[tx["ecu"]]["response"] for nrc in tx["negative_responses"])
                and (tx["positive_response"] is None or tx["positive_response"]["can_id"] == selected_mapping[tx["ecu"]]["response"])
                for tx in matched
            ) if matched else None,
            "pending_association_consistent": all(
                tx["response_pending_count"] == sum(nrc["payload"] == "7F 22 78" for nrc in tx["negative_responses"])
                for tx in matched if request == "22 F1 68"
            ) if matched and request == "22 F1 68" else None,
        }
        if request == "27 03":
            lengths_match = []
            for tx in positive:
                response_message = tx["positive_response"]
                for message in messages:
                    if (message["can_id"] == response_message["can_id"]
                            and message["timestamp"] == response_message["timestamp"]
                            and len(message["data"]) >= 2 and message["data"][0] >> 4 == 1):
                        expected = ((message["data"][0] & 15) << 8) | message["data"][1]
                        lengths_match.append(expected == len(bytes.fromhex(response_message["payload"])))
                        break
            checks[label]["multiframe_responses_checked"] = len(lengths_match)
            checks[label]["multiframe_lengths_match"] = all(lengths_match) if lengths_match else None
    return {"status": "checked_with_existing_configuration", "matching_ecu_pairs": best_pairs,
            "vehicle_identity_confirmed": False, "transactions": len(transactions), "services": checks,
            "pipeline_frames": result["parser_diagnostics"].pipeline_frames,
            "selected_channel_isotp_frames": {
                kind: sum(bool(m["data"]) and m["data"][0] >> 4 == value for m in messages)
                for kind, value in (("first", 1), ("flow_control", 3), ("consecutive", 2))
            }}


def validate_log(file_path=DEFAULT_LOG, *, channel=None, measure_memory=False):
    path = Path(file_path).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Validation input must be inside the project directory.")
    if not path.is_file():
        return {"status": "skipped", "reason": "Local DSA log is unavailable."}
    before = _fingerprint(path)
    discovery = ParserDiagnostics()
    start = time.perf_counter()
    channels = get_log_channels(path, diagnostics=discovery)
    discovery_seconds = time.perf_counter() - start
    selected = channels[0] if channel is None else channel
    diagnostics = ParserDiagnostics()
    start = time.perf_counter()
    messages = load_log(path, channel=selected, diagnostics=diagnostics)
    loading_seconds = time.perf_counter() - start
    if diagnostics.total_can_records != diagnostics.parsed_frames + diagnostics.skipped_frames:
        raise AssertionError("Parser frame accounting invariant failed.")
    if channels != diagnostics.channels or discovery.frames_by_channel != diagnostics.frames_by_channel:
        raise AssertionError("Channel discovery and message loading disagree.")
    uds = _uds_summary(path, selected, messages)
    diagnostics.pipeline_frames = uds.get("pipeline_frames", 0)
    report = {"status": "validated_with_warnings" if diagnostics.has_warnings else "validated",
              "file_size_bytes": path.stat().st_size, "diagnostics": asdict(diagnostics),
              "selected_channel_frames": diagnostics.selected_channel_frames,
              "channel_detection_seconds": round(discovery_seconds, 6),
              "message_loading_seconds": round(loading_seconds, 6),
              "timestamp_example_difference_ms": round((22.919897 - 22.915223) * 1000, 6),
              **_check_representative_records(path), "uds": uds}
    if measure_memory:
        tracemalloc.start()
        try:
            measured = load_log(path, channel=selected)
            report["message_loading_peak_python_mib"] = round(tracemalloc.get_traced_memory()[1] / 1024**2, 3)
            del measured
        finally:
            tracemalloc.stop()
    report["source_file_unchanged"] = before == _fingerprint(path)
    if not report["source_file_unchanged"] or not report["representative_records_match_including_padding"]:
        raise AssertionError("Read-only source or representative frame validation failed.")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", nargs="?", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--channel", type=int)
    parser.add_argument("--memory", action="store_true")
    arguments = parser.parse_args()
    try:
        report = validate_log(arguments.log_file, channel=arguments.channel, measure_memory=arguments.memory)
    except (OSError, ValueError, AssertionError) as error:
        # Exception strings may contain source filenames or offending input bytes.
        report = {"status": "error", "error_type": type(error).__name__, "reason": "Local DSA validation failed."}
    print(json.dumps(report, indent=2))
    return int(report["status"] == "error")


if __name__ == "__main__":
    raise SystemExit(main())
