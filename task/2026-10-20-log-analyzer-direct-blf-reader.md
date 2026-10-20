# Commit 7: Direct BLF reader and storage optimization

## Baseline and scope

Baseline HEAD was `9bd0d79b58293018b16495f2af69794cc3684440`; worktree was clean.
No commit was created. Original logs, vehicle configurations, licensing and
activation were not modified. No production threading/multiprocessing changed.

## Errno 28 investigation

The original incident is UNCONFIRMED: no failing traceback or failing-device
free-space measurements were supplied. We did not deliberately fill a disk.

The storage-expansion path IS confirmed from Commit 6 source:
`AnalysisWorker -> AnalysisController.fn_run -> run_pipeline -> load_log(.blf)
-> blf_to_asc -> can.ASCWriter -> load_asc`.

`blf_to_asc` chooses `Path(blf_file).with_suffix('.asc')`; ASCWriter opens it
for writing, so Analyze creates or overwrites an ASC beside the source BLF.
It is not a managed temporary file. There was no automatic output cleanup,
and exceptional conversion also lacked guaranteed reader/writer closing.
ASCWriter writes both while receiving messages and when flushing/closing.
A deterministic fault-injection test confirms ENOSPC propagation at its
`on_message_received` write path; this does not prove the original incident
failed at that same operation.

Channel discovery already iterated BLF without conversion, but lacked the new
shared file validation/error context. CopyService and ClipboardService only
resolve/read an existing sibling ASC; neither creates one. Existing atomic
configuration writes and Excel report writes are separate from BLF input.

## Architecture and compatibility

New Analyze path:
`worker -> controller -> pipeline -> load_log(.blf) -> load_blf -> can.BLFReader
-> normalized selected classic CAN messages -> unchanged ISO-TP/UDS/reports`.

No ASCWriter or temporary storage is used by BLF loading/discovery. ASC/TXT
dispatch and parser implementations are unchanged. Public `get_log_channels`
and `load_log` signatures (including optional diagnostics) remain compatible.

The normalized schema remains `timestamp`, `channel`, `can_id`, `dlc`, `data`.
Raw channel 0/1/2 maps to logical 1/2/3. Timestamp origin is the first yielded
BLF message, BEFORE channel/type filtering, matching the old ASCWriter path;
timestamps are rounded to six decimal places. Its legacy handling of a
timestamp earlier than that origin is also retained, not silently rebased.

Classic CAN data frames retain CAN ID, DLC 0..8 and bytes, including 29-bit IDs.
This avoids two old conversion/parser losses: short frames were rejected by
the ASC parser's minimum column count, and extended IDs had an `x` suffix
that its integer conversion rejected. Thus equivalent-result claims apply
to the legacy-supported input set; newly retained short/extended frames can
legitimately add results if a vehicle maps those CAN IDs. ASC behavior itself
was deliberately not changed.

FD, RTR, error and invalid data/channel frames are skipped with an aggregate
warning. Channel discovery retains the previous behavior of discovering all
channels exposed by BLFReader; a selected channel without supported classic
data gives a clear error. Filtering occurs while iterating, before retaining
normalized messages. Compressed input is handled by python-can containers,
not an application-level read of the entire raw BLF.

Malformed/short headers, declared file-size truncation, decoding errors and
non-padding incomplete final objects produce `Invalid or truncated BLF log`.
OSError retains errno and adds `Unable to read BLF log` context. Handles close
even on errors; no partial analysis result is returned. Existing worker failed
signals and warning-dialog paths handle these errors without GUI changes.

The explicit legacy `blf_to_asc` utility remains for callers/tests, not Analyze.
Its handles now close on failure. Explicit invocation can still overwrite
its chosen ASC output; it is not a safe automatic conversion path. No existing
user ASC is deleted. Benchmark ASC output is isolated and cleaned separately.

## Measured comparison

Input: `logs/280926_VF5NP_5Z.4.7.0 V4_ESC_Changecontent_P1.blf`, 31932182 bytes
(30.45 MiB), selected logical channel 1, identical WILD mapping in both modes.
This mapping choice is for controlled equivalence, not validation of the
vehicle identity suggested by the filename.

Windows/Python 3.12, python-can 4.6.1. Each trial used a fresh process; six
trials ran sequentially in reversed pairs: direct/old, old/direct, direct/old.
Earlier overlapping warmup runs were excluded. Time covers core pipeline
loading, ISO-TP, matching and report construction; not GUI rendering, channel
discovery or Excel export. RAM is OS process PeakWorkingSetSize, including the
interpreter/import baseline, not just Python allocations or virtual memory.

| Metric | Commit 6 workflow | Direct BLF |
| --- | --- | --- |
| Additional ASC bytes | 158425276 (151.09 MiB) | 0 |
| Input + intermediate logical bytes | 190357458 (181.54 MiB) | 31932182 (30.45 MiB) |
| Median analysis seconds | 82.850667 | 21.914165 |
| Analysis range, seconds | 81.457067..85.509808 | 21.853911..24.174915 |
| Median peak RAM, MiB | 36.097656 | 36.554688 |
| Peak RAM range, MiB | 36.085938..36.445313 | 36.113281..36.781250 |
| Messages passed into pipeline | 2486 | 2486 |
| Transactions | 134 | 134 |
| Statuses | OK 126, NRC_ONLY 4, TIMEOUT 4 | identical |

Disk figures are file logical sizes, not filesystem allocation/compression or
OS cache/pagefile measurements. No benchmark writes to the original ASC.

Raw trials (seconds / peak working-set bytes):
- Direct 1: 21.914165 / 38330368.
- Old 1: 82.850667 / 37838848.
- Old 2: 85.509808 / 38215680.
- Direct 2: 21.853911 / 38567936.
- Direct 3: 24.174915 / 37867520.
- Old 3: 81.457067 / 37851136.

All six result SHA-256 hashes match:
`e6138a24f865711ebdd9fb955bfa86464b19ef4c2a8910dcd06e8f3ce432d9c1`.

Additional real mixed CANFD/classic validation: `wild.blf`, channel 5, passes
68 messages and yields four transactions (1 OK, 3 NRC_ONLY). Its result hash
matches analysis of the existing, unmodified `wild.asc`:
`40196268112786e1f6e54bdc5fce1bbeb0c50a50f97018237688981c19eca8ee`.
This includes the delayed terminal NRCs fixed in Commit 6.

No RAM improvement is claimed. The selected benchmark channel retains only
2486 messages, so it is not a high-retention memory stress test. Pipeline
lists and reconstructed payloads still scale with selected traffic. A future
opt-in Memory Efficient Mode could filter mapped ECU request/response CAN IDs
before retention, with explicit handling of functional IDs and preserving the
original timestamp origin. That mode is NOT implemented here.

Reproduce each mode in separate processes, alternating their order:
```powershell
python -m tools.benchmark_blf 'logs/280926_VF5NP_5Z.4.7.0 V4_ESC_Changecontent_P1.blf' --mode old --channel 1
python -m tools.benchmark_blf 'logs/280926_VF5NP_5Z.4.7.0 V4_ESC_Changecontent_P1.blf' --mode direct --channel 1
```
The opt-in benchmark's old mode needs space for its isolated ASC, even though
production Analyze no longer needs such storage. Temporary directories are
created only by this diagnostic tool/tests, under the workspace, and cleaned.

## Verification and limitations

- New tests first reproduced ASC creation/overwrite, lost short/extended frames,
  silent truncation and unclear errors before implementation.
- Regression suite: 142 tests, 141 passed, one existing Excel expectation failed.
  `test_export_workbook_applies_shared_table_style_to_all_sheets` expects BCM at
  Summary A2, but the existing banner makes A2 the `ecu` header. Reproduced using
  the exact Commit 6 export source loaded in memory; left unchanged.
- Final rerun excluding that independently confirmed baseline test: 141/141
  passed. `git diff --check` also passed; no benchmark temporary directory remains.
- Tests cover channels 1/2/3, missing channel, IDs/DLC/bytes, epoch/microsecond
  timestamps, SF/MF ISO-TP, RoutineControl, delayed pending final responses,
  ASC equivalence, DSA-TXT, workbook contents, Qt ResultTable/Quick Filter,
  no ASC writer call even when it would raise ENOSPC, existing ASC protection,
  malformed/truncated/unreadable BLFs, bounded raw reads across containers,
  and real failed signals from both workers.
- Syntax compilation passed for all ten changed/new Python files.
- No new dependency was added. There was no manual desktop or physical ECU run.
- Some validation uses python-can 4.6.1 header constants and its partial-object
  tail state. Re-test this adapter before changing the pinned python-can version.
  This is not a complete forensic validator for every possible BLF corruption
  or unknown object/compression type; library warnings/skips still apply.
- Copy raw log still requires an existing ASC. Removing implicit conversion
  means Analyze no longer supplies one for that separate legacy feature.
- Excel export/explicit conversion/other application writes can independently
  fail with ENOSPC. No new storage exhaustion occurred in direct analysis;
  a future occurrence needs its traceback to identify the actual operation.

## Modified files

- `core/blf_reader.py` (new)
- `core/asc_reader.py`
- `core/convert_blf.py`
- `tests/core/test_blf_reader.py` (new)
- `tests/core/test_log_channels.py`
- `tests/core/test_dsa_pipeline.py`
- `tests/core/test_dsa_txt_parser.py`
- `tests/core/test_response_pending.py`
- `tests/gui/test_blf_errors.py` (new)
- `tools/benchmark_blf.py` (new)
- `task/2026-10-20-log-analyzer-direct-blf-reader.md` (this report)

## Sources

- [python-can 4.6.1 BLFReader](https://python-can.readthedocs.io/en/v4.6.1/file_io.html#can.BLFReader)
- [BLF implementation](https://python-can.readthedocs.io/en/v4.6.1/_modules/can/io/blf.html)
- [ASCWriter timestamp/channel implementation](https://python-can.readthedocs.io/en/v4.6.1/_modules/can/io/asc.html)
- [Windows process memory counters](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters)
- [GetProcessMemoryInfo](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo)

Suggested commit message: `log analyzer - direct blf reader commit 7`.
