---
name: can-m04b-continuous-can-blf
summary: Extend the verified Commit 57 CAN/UDS implementation with continuous Classical CAN RX monitoring and standards-compatible BLF logging, without changing the existing UDS workflow or implementing Security Access.
---

# V-CODE — M04-B: Continuous CAN Monitor + BLF Recording

## 0. Mission, baseline and boundaries

You are a senior automotive integration and validation software engineer working in Python 3.12, PySide6 6.11.1, python-can 4.6.1, can-isotp 2.0.7 and Vector XL Driver.

- Repository: `dathp95/UDS-Analysis`.
- Exact baseline: Commit 57, `87b3cb37ecd5cf406bff5d3c2cf49462bbda0159`.
- Prerequisite: existing `22 F1 90` physical, normal 11-bit UDS requests work with Vector hardware; preserve this behavior exactly.
- **Only** implement M04-B: continuous raw CAN monitoring, reliable BLF recording, optional CSV export from the retained monitor buffer, hardware-free tests and documentation.
- Do not implement Security Access (SID `0x27`), seed-key DLL, cyclic sending, raw-frame transmit UI, diagnostic batch runner, CAN FD or flashing.
- No fake CAN responses or invented bus availability; distinguish tests with fake buses from real-hardware validation.
- Do not create a Git commit or push automatically.

## 1. Mandatory reconnaissance before modifying code

Read the CURRENT content of these paths and identify the actual signal ownership and resource boundaries:

1. `gui/tabs/can_interface_tab.py`
2. `gui/controllers/can_connection_controller.py`
3. `gui/controllers/can_diagnostic_controller.py`
4. `gui/workers/can_connection_worker.py`
5. `gui/workers/can_diagnostic_session.py`
6. `gui/widgets/can_interface/can_monitor_panel.py`
7. `gui/widgets/can_interface/diagnostic_table_panel.py`
8. `services/can/can_service.py`
9. `services/can/vector_backend.py`
10. `services/can/owned_vector_bus.py`
11. `services/can/isotp_transport.py`
12. `services/can/diagnostic_client.py`
13. `core/can_interface_view.py`
14. `core/diagnostic_request.py`
15. `services/can/can_connection.py`
16. `models/ecu.py`, `services/vehicle_service.py`, `repositories/vehicle_repository.py`
17. `config/paths.py` and project theme/style controls
18. Existing M01–M04 CAN tests and `docs/can_interface/M03_UI_LAYOUT_REPORT.md`.

Confirm installed python-can BLF APIs and source, especially timestamp expectations, `Message.is_rx`, channel numbering conversions and `BLFWriter.stop()` finalization. Use pinned 4.6.1 behavior; do not assume source of `main` matches the pinned version.

Read back the existing M04 request test fixture: transmit `03 22 F1 90 00 00 00 00`, receive `10 14 ...`, transmit `30 00 00 ...`, receive `21 ...` and `22 ...`.

### Review findings that must inform implementation

- `CanDiagnosticSession` currently starts its 2-ms QTimer only while a manual diagnostic is running.
- The same `CANConnectionWorker`/`CANConnectionTask` owns the native CAN bus and executes connection/disconnection.
- `CANService.fn_begin_diagnostic` owns a non-blocking operation lease; do not accidentally make the idle monitor hold the exclusive diagnostic lease forever.
- `VectorBackend.fn_receive_frame()` currently calls `bus.recv(timeout=0.0)`.
- `VectorBackend.fn_send_frame()` reports driver-accepted TX; TX echo can also appear as a received bus event.
- `CanFrameView` includes relative timestamp, wall timestamp, monotonic timestamp, channel, extended, RTR/error flags and TX origin.
- `CANConnectionTask` has a bounded 4096-frame **UI** queue and batch signal every 75 ms.
- `CanMonitorPanel` retains at most 2000 displayed frame records; it is NOT a lossless logging source.
- `CanMonitorPanel.btn_export` and `btn_blf` are currently intentionally disabled.

## 2. Architecture: single CAN RX owner, multiple data consumers

Required conceptual flow:

```
Vector native CAN bus (ONE instance)
  └─ Existing connection-owner QThread
       ├─ cooperative CAN RX pump (idle and during diagnostics)
       ├─ existing ISO-TP / UDS state machine
       ├─ TX acceptance + observed TX echo handling
       └─ immutable raw CAN event stream
            ├─ bounded UI queue → CanMonitorPanel (noncritical)
            └─ independent recording queue → BLF writer (critical)
```

### Hard ownership rules

- Never create a second Vector CAN bus for monitoring.
- Never start a second concurrent `bus.recv()` consumer.
- Keep all native `send`, `recv`, and `shutdown` coordinated through the existing owner thread.
- Do not access `bus` directly from a QWidget or disk-writer thread.
- Do not run a blocking receive loop inside a Qt slot that starves queued Connect/Disconnect/UDS requests.
- Use cooperative QTimer polling (or a carefully justified equally safe equivalent); bound frames/time processed in each iteration.
- Ensure new idle monitoring does not block `CANService.fn_begin_diagnostic()` and existing operation lock.
- When diagnostic begins, the same receive owner routes frames to both raw capture and ISO-TP, never consuming frames twice.
- Preserve response correlation, Flow Control, NRC 0x78, timeout and cancellation behavior.
- On device loss, report a real driver fault, stop monitoring/recording appropriately, and obey M02 RECOVERY_REQUIRED/rediscovery lifecycle.

## 3. Stage B01 — Introduce a canonical, immutable raw event contract

Prefer a well-scoped immutable raw event model in `core/` or `services/can/`. Reuse/extend `CanFrameView` only if backward-compatible, avoiding duplicate divergent frame structures.

A raw record must preserve:

- CAN identifier, standard/extended flag
- original data bytes, actual DLC, RTR/error flags
- RX/TX direction and explicit TX origin (`driver_accepted` versus observed `echo`)
- source physical/local channel and original metadata, if known
- monotonic event time used for internal sequencing
- absolute Unix-wall timestamp in seconds suitable for BLF
- a monotonic sequence number or stable ordering strategy for same-timestamp events
- owning connection/session generation, so reconnect cannot mix sessions

Do not reformat the bytes at the acquisition boundary. Keep text conversion in presentation/export adapters.

### Time origin requirements

- RX `python-can.Message.timestamp` might be a Unix epoch timestamp for Vector but must be validated on actual hardware and fakes. Handle missing/invalid timestamps explicitly.
- TX accepted events need a wall timestamp associated with the send call.
- Establish one wall/monotonic anchor per CAN connection/session for fallback. Do not use elapsed GUI Time(s) as a Unix BLF timestamp.
- Keep acquisition order stable; never silently reverse TX/FF/FC/CF order.
- Do not fabricate nanosecond hardware precision from application polling.
- Record source/timestamp policy in report and unit tests.

### Channel requirements

- The Vehicle Manager's UDS Request/Response IDs are **not** BLF channels.
- Vector channel selection contains local `channel`, global `channel_index`, `hw_channel`, and hardware identity. Do not interchange them.
- Examine python-can 4.6.1 BLFWriter: `Message.channel` can be interpreted as zero-based and incremented by the writer; default writer channel may be one-based.
- Normalize selected local hardware port to the correct BLF channel number; test both first and second physical channels.
- If a mapping cannot be validated, surface it and do not silently write wrong channel metadata.

## 4. Stage B02 — Persistent cooperative CAN receive pump

Refactor the smallest necessary portion of `CanDiagnosticSession` or add a well-defined `CanIoPump` subordinate to the existing `CANConnectionWorker`.

The receive pump should:

- Start when the CANService has reached CONNECTED, and stop before bus shutdown.
- Drain a bounded number of frames per timer tick; adapt per-tick budget to avoid GUI starvation under traffic.
- Keep monitoring idle traffic (e.g. repeated 0x760 frames in the user's capture) before, during and after manual UDS requests.
- Offer runtime `Monitoring` / `Stopped` state visibly in `CanMonitorPanel`.
- Continue to pass every eligible received frame to the existing active diagnostic client during a request.
- Route all raw TX/FC/CF and RX frames through one source stream exactly once according to the echo policy.
- Protect transaction deadlines and never stall ISO-TP because the GUI cannot refresh or the file system is slow.
- Avoid unbounded Qt signals or growing deques.
- Explicitly test disconnect while idle monitoring and during ISO-TP First Frame/Consecutive Frame handling.

**Do not start/stop `bus.recv` in the GUI. Do not let the monitor own the driver.**

## 5. Stage B03 — Implement independent BLF writer service

Create a dedicated feature service, e.g. `services/can/blf_recording_service.py`, plus a writer worker only if necessary.

Use `python-can==4.6.1` `can.BLFWriter`. Do not hand-serialize Vector's proprietary BLF binary format.

Recommended lifecycle:

```
STOPPED → STARTING → RECORDING → STOPPING → STOPPED
                    └──── ERROR/INCOMPLETE (when necessary)
```

### Requirements

1. User starts recording from the existing `Start BLF Log` button. Never start silently when opening the app.
2. Select destination with Save File dialog; default directory under `output/CAN_Interface_Logs/` (add named path constant under `config/paths.py`).
3. Suggested filename: `V_CODE_CAN_<vehicle>_<YYYYMMDD_HHMMSS>.blf`. Sanitize filename; vehicle is optional.
4. No overwrite without explicit user confirmation; avoid `append=True` as the default.
5. Write actual Classical CAN frames including unrelated traffic, diagnostic request, ECU responses, FC, and CF when present.
6. Convert canonical events into `can.Message` correctly: `arbitration_id`, `is_extended_id`, `is_remote_frame`, `is_error_frame`, `dlc`, `data`, `channel`, `is_rx`, and **Unix timestamp**.
7. Use a dedicated bounded recording queue separate from the monitor/UI queue. Do not rely on the 2000-row GUI buffer or `frame_batch` GUI delivery.
8. Disk writing must not block native CAN receive/ISO-TP timing; use an orderly writer executor/worker, with a single writer owner.
9. Track frames captured, written, and dropped/rejected, plus error status, from the actual recording pipeline.
10. If recording queue overflows, disk fails, or a timestamp is impossible to normalize, **mark recording incomplete/error**; do not report a perfect valid complete trace.
11. On Stop: stop accepting new recording events at a clearly defined boundary, drain accepted queue in order, invoke `BLFWriter.stop()` exactly once, then mark finalized.
12. On Disconnect: stop new CAN RX, finalize pending recorder records, and preserve existing connection cleanup order. A recording writer failure must not forcibly corrupt the native CAN resource state.
13. On application close: orderly finalize the BLF file and signal completion; no fire-and-forget writer left writing after Qt shutdown.
14. Ensure two simultaneous starts cannot open two writers to the same path.
15. Do not overwrite BLF fields or invent RX/TX directions due to monitor presentation choices.
16. Preserve previous BLF files when the next recording session starts.
17. Handle empty recording sessions deliberately (valid empty file or remove unused file: pick and document one consistent policy).
18. Do not claim CANoe/TSMaster compatibility merely because BLFWriter returned without exception.

### TX echo policy

Current backend emits `driver_accepted` TX immediately after `bus.send()` succeeds and may later receive `observed_echo` TX. Define one deterministic, tested export policy to prevent unintended duplicate log entries. Prefer one logical TX record per actual send for the normal test path. A driver-accepted TX is not proof of physical network acknowledgment. Preserve origin detail internally for future diagnostics.

Do not deduplicate unrelated periodic RX frames just because CAN ID/data or rounded timestamps are identical.

## 6. Stage B04 — Wire existing CAN Monitor UI without a redesign

Reuse the current `CanMonitorPanel` structure and V-CODE theme/style controls:

- `PrimaryTable`, `PrimaryLineEdit`, `PrimaryComboBox`, `ActionButton`
- `ThemeManager`, `fn_apply_scrollbar_style` and existing panel style.
- The existing table columns remain Time(s), Dir, CAN ID, DLC, Data(HEX).
- Current CAN ID and direction filters remain UI-only and MUST NOT filter BLF recording.
- `Clear` clears only the UI view/buffer, not device RX queue and not the BLF file.
- Enable `Start BLF Log` when connected and writer is ready; change to `Stop BLF Log` when recording; show RECORDING / STOPPING / ERROR statuses and file name/location in tooltip/status panel.
- Enable `Export CSV` only when retained monitor data exists. Export is best-effort retained-view content, not promised lossless capture.
- Keep `Run Selected` disabled; no batch sequence execution.
- No new ECU ID/DLL editors in the CAN Interface.
- Avoid O(visible_rows × all_batches) full-table rebuild at sustained bus traffic. Use an incremental, batched table update or a justified `QAbstractTableModel` if needed. Keep memory bounded.
- Preserve Light/Dark theme, compact buttons, current splitter layout and Save Order.
- Avoid showing all frames with the same app timestamp simply because they were polled in one tick. When the driver provides usable timestamps, keep their relative differences.

## 7. Stage B05 — Optional CSV export from retained view

If achievable without destabilizing BLF, implement the already-present `Export CSV` button.

- Export only currently retained frames, document whether UI filters apply.
- Columns: Absolute Timestamp, Elapsed Time (s), Direction, Channel, CAN ID, Extended, DLC, Data (HEX), TX Origin.
- Use UTF-8 with BOM for Excel compatibility, and CSV module quoting.
- Never represent a 2000-frame display buffer as a complete raw log.
- Prefer keeping CSV export independent of BLF recorder memory.
- If CSV scope threatens the critical BLF/continuous RX quality, explicitly defer CSV rather than cutting safety testing.

## 8. Stage B06 — Round-trip verification and interoperability

Automated test plan (mock bus, virtual CAN fixtures, temporary directories; no Vector hardware dependency):

1. Idle CAN frames appear without sending any UDS.
2. Single native bus and exactly one RX consumer through Connect → UDS → Disconnect.
3. Existing `22 F1 90` request still transmits SF, receives FF, transmits FC, receives CF1/CF2 and passes prefix expectation.
4. During UDS RX, both reassembly and raw recording see the same frames without racing.
5. Recorder captures unrelated periodic frames such as `0x760` even outside diagnostic transaction.
6. Distinct periodic frames with identical ID/data are preserved; no content-based RX dedup.
7. TX echo policy prevents duplicate logical transmit records.
8. BLF includes real TX direction and real RX direction, correct CAN ID, bytes, DLC and channel.
9. BLF has valid Unix timestamps, monotonic/nondecreasing time policy, and correct relative timing.
10. First and second Vector local channel mapping are serialized/read correctly.
11. Start/Stop multiple sessions, unique filenames, refused overwrite.
12. Disk write or BLFWriter.stop failure is shown as ERROR/INCOMPLETE, never successful finalization.
13. Recording queue overflow tracks missing records and marks incomplete.
14. GUI monitor queue overflow/drop does not itself discard records from writer queue.
15. Clearing or filtering monitor does not clear/filter BLF recording.
16. Disconnect while recording finishes valid file; test proper cleanup order.
17. Application shutdown while recording stops writer and owner thread without native use-after-close.
18. Device unplug causes graceful failure and no fake clean capture.
19. High-rate fake input keeps GUI responsive, RX serviceable, ISO-TP deadlines honored.
20. Baseline M01/M02/M03/M04 regression tests pass, including `test_isotp_transport.py`, `test_diagnostic_client.py`, `test_can_diagnostic_io.py`, `test_can_diagnostic_execution.py`.
21. Negative UDS and NRC 0x78 behavior remains unchanged.
22. No Security Access/seed-key execution added.
23. Empty or tiny BLF writer finalization policy tested.
24. Theme, sidebar save order, comment persistence, table per-row action unchanged.

### Round-trip BLF tests

For each test recording:

```
writer = can.BLFWriter(destination)
# Feed canonical actual/fake raw frames converted to can.Message.
writer.stop()
messages = list(can.BLFReader(destination))
# Verify IDs, data, is_rx, channel, timestamps, count and expected sequence.
```

Use the actual writer service, not an isolated BLFWriter-only smoke test, for integration assertions. If suitable, use repo `core/blf_reader.py` or `core/convert_blf.py` to verify V-CODE's existing reader accepts the output; ensure no private project files are modified.

### Windows hardware acceptance (manual; cannot be simulated)

- Connect VN1630A or VN1640A on an isolated correctly terminated test/bench CAN network.
- Confirm CAN Monitor displays idle periodic traffic when no UDS request is running.
- Press Start BLF Log before sending VIN request; send Read VIN to selected ECU.
- Confirm BLF captures `TX request → RX First Frame → TX Flow Control → RX CF1/CF2` with correct IDs and bytes.
- Press Stop; verify generated `.blf` is readable via python-can `BLFReader` and V-CODE Log Analyzer.
- Open exact generated `.blf` in **CANoe** and **TSMaster**; document actual product versions and whether they open successfully, preserve direction, channels and timestamps. No blanket compatibility claims from unit tests.
- Compare one generated log with user-provided reference `.blf` at the semantic CAN-frame level, not proprietary metadata byte-for-byte.
- Reconnect, start new recording, unplug hardware, simulate high bus traffic, and terminate V-CODE during active recording; verify graceful output/error reporting.
- Do not send arbitrary frames on a production vehicle network.

## 9. Explicit non-goals and safeguards

Do not implement any of the following in M04-B:

- Security Access (0x27), any seed/key derivation or DLL loading
- DiagnosticSequence batch execution; no automatic Run Selected
- Changing request/response IDs outside Vehicle Manager
- CAN FD, LIN, DoIP, FlexRay, J1939 or multi-channel simultaneous capture
- Raw frame TX editor, retransmit/replay, cyclic transmit
- New licensing or persistence schema outside well-scoped logging preferences
- Any rewrite of working ISO-TP logic merely to add recording
- Silent fake responses, fake Passed/Failed, or fabricated frame timestamps

Keep the original output's frame count and observed direction meaningful: CAN traffic visible in the user's current monitor screenshot is a real capture, but identical values appearing frequently on bus must not be misclassified as duplicated software frames without evidence.

## 10. Required deliverables and commit boundary

Prefer a small set of focused files and clean responsibilities. Suggested architecture (adapt to actual repo patterns):

- `core/can_raw_event.py` — canonical immutable event or minimally extended compatible existing model
- `services/can/can_capture.py` — capture fan-out and bounded drop metrics, if justified
- `services/can/blf_recording_service.py` — writer lifecycle and BLF conversion
- `gui/workers/can_blf_writer_worker.py` — writer-owned background file executor, if justified
- `gui/workers/can_diagnostic_session.py` — refactor into single continuous cooperative CAN RX pump (or compose pump)
- `gui/workers/can_connection_worker.py` — single owner integration, no extra bus
- `gui/widgets/can_interface/can_monitor_panel.py` — button/state wiring and performance
- `gui/controllers/can_diagnostic_controller.py` / new `can_recording_controller.py` — GUI signals and lifecycle glue
- `gui/tabs/can_interface_tab.py` — ONLY component composition/wiring
- `config/paths.py` — output directory constant
- `tests/services/` and `tests/gui/` — targeted tests
- `docs/can_interface/M04B_CAN_MONITOR_BLF_REPORT.md` — report

The report MUST include:

1. Baseline commit SHA.
2. Architecture diagram and exact bus/thread ownership.
3. Continuous RX state transitions and interaction with UDS.
4. Timestamp policy, BLF channel numbering, RX/TX echo policy.
5. Logging queue backpressure/drop policy and guarantee limits.
6. Lifecycle/cleanup and invalid-file/finalization failure handling.
7. Changed files and unit tests actually run; failures distinguished from preexisting ones.
8. Python-can BLFReader round-trip details.
9. Manual CANoe/TSMaster hardware test checklist and untested items.
10. Explicit statement that Security Access is still unavailable.

Suggested commit title (do NOT commit):

`CAN Interface - M04B Continuous Monitor and BLF Logging`

## 11. Definition of done

- Connected Vector bus receives raw CAN frames continuously and safely.
- One bus / one native RX consumer remains true during idle, UDS and shutdown.
- Existing real UDS Read VIN transaction remains correct.
- Start and Stop BLF controls work; the file is finalized and can be read back.
- BLF contains real TX/RX and unrelated bus traffic (when present), preserving original bytes and valid timestamps/channels.
- GUI remains responsive under sustained CAN traffic, with bounded monitor memory.
- Recorder failures and drops are visible; no false "Complete" state.
- All targeted regression tests pass.
- Security Access stays blocked.
- CANoe/TSMaster compatibility is marked *unverified* until opened successfully on Windows hardware.
