"""Measure one BLF pipeline in a fresh process; never overwrite a source ASC.

Run old/direct modes separately, alternating the order across repeated runs.
Example: python -m tools.benchmark_blf logs/wild.blf --mode direct --channel 5
"""

import argparse
import ctypes
import hashlib
import json
import os
import tempfile
import time
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import can

from core.asc_reader import load_asc, load_log
from core.pipeline import run_pipeline
from models.ecu import ECU
from models.vehicle import Vehicle


ROOT = Path(__file__).resolve().parents[1]


def peak_rss_bytes():
    if os.name == "nt":
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in (
                    "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                    "PagefileUsage", "PeakPagefileUsage")]

        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        get_memory = ctypes.WinDLL("psapi", use_last_error=True).GetProcessMemoryInfo
        get_memory.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        get_memory.restype = wintypes.BOOL
        if not get_memory(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return counters.PeakWorkingSetSize
    import resource
    import sys
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def benchmark(path, mode, channel, vehicle_name):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Benchmark inputs must be inside the workspace.")
    config_dir = (ROOT / "config" / "vehicles" / vehicle_name / "ecus").resolve()
    if not config_dir.is_relative_to(ROOT / "config" / "vehicles"):
        raise ValueError("Vehicle config must be inside the workspace.")
    ecus = []
    for config in sorted(config_dir.glob("*.json")):
        data = json.loads(config.read_text(encoding="utf-8-sig"))
        ecus.append(ECU(name=config.stem, request_id=data["request_id"], response_id=data["response_id"]))
    if not ecus:
        raise ValueError("Vehicle has no ECU configuration.")
    vehicle = Vehicle(name=vehicle_name, ecus=ecus)
    message_count = 0
    disk_bytes = 0
    with tempfile.TemporaryDirectory(prefix="blf_benchmark_", dir=ROOT) as directory:
        destination = Path(directory) / "converted.asc"

        def measured_load(file, channel=None):
            nonlocal message_count, disk_bytes
            if mode == "old":
                # Same conversion loop as Commit 6, but with an isolated output.
                with can.BLFReader(file) as reader, can.ASCWriter(str(destination)) as writer:
                    for message in reader:
                        writer.on_message_received(message)
                disk_bytes = destination.stat().st_size
                messages = load_asc(destination, channel=channel)
            else:
                messages = load_log(file, channel=channel)
            message_count = len(messages)
            return messages

        baseline_peak = peak_rss_bytes()
        start = time.perf_counter()
        with patch("core.pipeline.load_log", measured_load):
            result = run_pipeline(str(path), vehicle, channel=channel)
        seconds = time.perf_counter() - start
        peak = peak_rss_bytes()
        additional_files = [item.name for item in Path(directory).iterdir()]
    return {
        "mode": mode, "input": path.name, "input_bytes": path.stat().st_size,
        "channel": channel, "vehicle": vehicle_name, "python_can": can.__version__,
        "intermediate_bytes": disk_bytes, "intermediate_files": additional_files,
        "baseline_peak_rss_bytes": baseline_peak, "peak_rss_bytes": peak,
        "analysis_seconds": round(seconds, 6), "pipeline_messages": message_count,
        "transactions": len(result["transactions"]),
        "statuses": dict(Counter(tx["status"] for tx in result["transactions"])),
        "result_sha256": hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file")
    parser.add_argument("--mode", choices=("old", "direct"), required=True)
    parser.add_argument("--channel", type=int, default=None)
    parser.add_argument("--vehicle", default="WILD")
    args = parser.parse_args()
    print(json.dumps(benchmark(args.log_file, args.mode, args.channel, args.vehicle)))


if __name__ == "__main__":
    main()
