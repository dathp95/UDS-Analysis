# V-CODE — Milestone 04: Real UDS Communication (Non-Security)

## Role and baseline

You are a senior automotive diagnostic software engineer developing V-CODE, a Python 3.12 / PySide6 6.11.1 / python-can 4.6.1 Windows application using Vector VN hardware.

Repository: `dathp95/UDS-Analysis`.

Baseline: commit `16e874f44e8e6d63d8dd619404a5ab1ed2a9d496` (`can interface - commit 56`).

**Implement one genuinely working per-row UDS request/response path, including Classical CAN ISO-TP single-frame and multi-frame support. Never simulate ECU success. Do NOT implement or issue SecurityAccess service 0x27, seed/key DLLs, flashing, or automated sequence execution.**

Implement sequentially, testing each checkpoint. Do not commit/push automatically.

## 1. Mandatory source review — before coding

Read the latest versions of:

- `gui/tabs/can_interface_tab.py`
- `gui/controllers/can_connection_controller.py`
- `gui/controllers/can_workspace_controller.py`
- `gui/widgets/can_interface/diagnostic_table_panel.py`
- `gui/widgets/can_interface/sequence_sidebar.py`
- `gui/widgets/can_interface/can_monitor_panel.py`
- `gui/widgets/can_interface/session_panel.py`
- `gui/widgets/can_interface/current_test_case_panel.py`
- `gui/workers/can_connection_worker.py`
- `gui/workers/can_discovery_worker.py`
- `services/can/can_service.py`
- `services/can/vector_backend.py`
- `services/can/owned_vector_bus.py`
- `services/can/can_connection.py`, `can_config.py`, `can_device.py`
- `models/vehicle.py`, `models/ecu.py`
- `services/vehicle_service.py`, `repositories/vehicle_repository.py`
- `core/diagnostic_sequence.py`
- `repositories/diagnostic_sequence_repository.py`
- `core/diagnostic_sequence_import.py`
- `repositories/can_sequence_repository.py`
- `core/can_interface_view.py`
- `docs/can_interface/M01_DEVICE_DISCOVERY_REPORT.md`
- `docs/can_interface/M02_CONNECTION_MANAGEMENT_REPORT.md`
- `docs/can_interface/M03_UI_LAYOUT_REPORT.md`
- `requirements.txt` and relevant tests.

Use existing `.diag` test fixtures as data-only examples, not hardware proof. The M03 report explicitly says its four fixtures are synthetic, so do not claim they are the original uploaded files. Inspect the live repo before naming or editing any method not present.

## 2. Exact user workflow / acceptance example

1. User connects VN1630A/VN1640A to the test bench and discovers the intended CAN channel.
2. User selects an existing Vehicle package in the M03 CAN Interface table, e.g. `VF5NP`.
3. User opens the `READ VIN` sequence and locates the row whose ECU is `BCM` and Payload is `22 F1 90`.
4. User clicks that row's `>` button. This action is independent of the row checkbox.
5. Resolve the ECU from the **currently selected Vehicle** through `VehicleService.load_vehicle(vehicle_name).ecus`, never from the `.diag` embedded `IDReq`, `IDResp`, or `DLLFile`.
6. For actual `VF5NP/BCM`, repository data currently uses `request_id="681"` and `response_id="601"`. Treat them as **hex strings**: CAN TX ID `0x681`, RX ID `0x601`; NOT decimal 681/601.
7. Send **UDS payload** bytes `22 F1 90`, not an 8-byte hand-composed CAN frame from the table.
8. Automatically perform ISO-TP framing and flow control. A plausible vehicle trace for this case is:

   ```text
   CAN TX 0x681  03 22 F1 90 00 00 00 00
   CAN RX 0x601  10 14 62 F1 90 4D 47 55
   CAN TX 0x681  30 00 00 00 00 00 00 00
   CAN RX 0x601  21 56 35 4A 54 4C 58 54
   CAN RX 0x601  22 4A 39 39 39 37 34 31
   ```

   This is a known illustrative trace, **not a command to transmit automatically to a live vehicle**. Exact padding/flow-control fields must be governed by a documented configuration and protocol state.
9. Display the **reassembled UDS payload**, without ISO-TP PCI bytes, in `Receive Message`:

   `62 F1 90 4D 47 55 56 35 4A 54 4C 58 54 4A 39 39 39 37 34 31`

10. Compare with `Expected Response="62 F1 90"` using the step's `match="prefix"`; mark **Passed** if it matches.
11. Show each actual CAN TX/RX physical frame in CAN Monitor, with truthful direction and timestamps.

**Never present this sample response as if received from hardware.**

## 3. Narrow scope

### In scope

- Manual **one-row-at-a-time** request, via existing `row_send_requested(step_id)`.
- One active diagnostic transaction at a time, targeted at the selected physical ECU.
- Normal physical addressing for Classical CAN, initially 11-bit IDs; allow explicit/validated 29-bit support only if tested and fully specified.
- ISO-TP SF/FF/CF/FC for request and response; receive reassembly and transmit segmentation.
- Basic positive and negative UDS response classification, NRC 0x78 pending logic.
- Timeouts, errors, cancellation, disconnect integration.
- Real CAN Monitor updates from the same native bus (no fake frames).
- Mapping received payload to the original row and its expected-response match rule.
- Mocked unit/integration tests and a separate physical bench checklist.

### Explicitly out of scope

- SecurityAccess `0x27` in any form; seed request, key request, DLL load or key generation.
- Any implicit security unlock prior to other requests.
- Bulk `Run Selected` / multi-sequence runner / timed repeats; keep these disabled.
- Automatic cyclic CAN TX, Raw Frame editor, flashing, programming, CAN FD.
- Full UDS feature browser, DBC/ODX decoding, hotplug polling.
- Actual BLF file writing or CSV export **unless requested as a separate milestone**. Preserve the M03 disabled BLF/CSV controls. Create a clean raw-frame event contract for future BLFWriter integration.

## 4. Implementation phases — keep responsibilities separate

### M04-01 — Typed contracts and ECU resolver

Prefer a pure service/core module for:

- `DiagnosticRequest`: immutable transaction ID, stable `step_id`, document/source generation ID, vehicle name, ECU name, tx CAN ID, rx CAN ID, extended flag, `uds_payload: bytes`, expected bytes, match mode, settings.
- `DiagnosticResult`: immutable `step_id`, full `response_payload: bytes | None`, status, NRC, human-readable error, timing, transaction ID/generation.
- `DiagnosticOutcome`: typed enum or equivalent containing `Passed`, `Failed`, `Timeout`, `Error`, `Not Evaluated`, and `Cancelled` mapped deliberately to supported UI outcomes.
- Optional `IsoTpSettings` / `DiagnosticTiming` with explicit tested defaults.

Create an ECU resolver, not a second Vehicle database. Read the **selected Vehicle**, find **exactly one** ECU matching the row's ECU name, and parse `ECU.request_id` / `ECU.response_id` as hexadecimal (e.g., `int(value.strip(), 16)`, handling an optional `0x` prefix). Validate 11-bit range `0x000..0x7FF` or explicit 29-bit mode. For IDs above 11-bit range, require a supported 29-bit addressing path rather than silently truncating or treating them as 11-bit.

`models.ecu.ECU.resources['dll']` exists but must NOT be loaded. The `.diag` source may contain IDs/DLL paths; ignore them as canonical transport config.

Check that selected Vehicle has not changed since the row's request snapshot; freeze request data before dispatch. Avoid alias guessing, name collisions, fallback to another ECU, and implicit vehicle auto-selection.

Build the pure resolver and test it **before touching Vector native I/O**.

### M04-02 — Safe transport owner and raw frame path

M02 currently creates a **persistent `CANConnectionTask` / `CANConnectionWorker` QThread**, and `VectorBackend` owns one native VectorBus. Preserve this design and cleanup rules.

Create a **single receive owner** per physical bus and a coordinated TX path. Do NOT have a second worker independently call `bus.recv()` while the diagnostic stack also calls `recv()`. No second `can.Bus()` instance. GUI code must never access `_bus` directly.

Preferred: extend the existing M02 owner worker with a cooperative, bounded I/O pump scheduled on its QThread event loop (e.g., a timer), with **one** bus RX consumer; route each real RX frame to (1) ISO-TP transaction engine and (2) bounded monitor event sink. Queue/serialize TX on the same owner. Bound work per iteration so Qt queued Connect/Disconnect/cancel callbacks are not starved. Do not use a never-returning `while True: bus.recv(...)` in a worker slot.

Alternative acceptable only with documented tests: a dedicated isolated transport thread/executor with an explicit bus ownership transfer or audited serialization, plus provably ordered stop/cleanup. Avoid incidental `can.Notifier`, `CanStack`, or additional RX threads without reconciling ownership and receipt of every CAN frame. Review `python-can-isotp` 2.x behavior: `TransportLayer.start()` owns internal threads; cooperative `TransportLayerLogic` is available for externally managed processing. Choose one mechanism after checking installed APIs and demonstrate cancellation, FC timings, cleanup and monitor fanout in tests.

Add raw frame event models that preserve: wall-clock CAN timestamp, monotonic/relative display timestamp, channel, arbitration ID, extended flag, DLC, bytes, RX/TX, and the distinction between driver-accepted TX versus observed TX echo. Update `CanFrameView` minimally if necessary. Do not infer extension from ID length if hardware gives an explicit flag.

A successful `send()` call means driver accepted a CAN frame, **not** that ECU received it.

### M04-03 — ISO-TP for Classical CAN

Use a well-maintained, explicitly version-pinned library if suitable (`can-isotp` 2.x / `isotp.TransportLayerLogic`), or a separately tested minimal ISO-TP implementation if required for ownership. Do NOT hand-code an incomplete 'look for 0x10 then concatenate 0x21/0x22' parser.

Supported now:

- Normal 11-bit physical addressing (`txid`, `rxid`) with different IDs.
- Classical CAN 8-byte data maximum; documented optional 8-byte zero padding for application interoperability, without placing padding in UDS payload.
- Single Frame (SF), First Frame (FF), Consecutive Frames (CF) with sequence counter modulo 16, and Flow Control (FC: Continue/Wait/Overflow).
- Both multi-frame RX (VIN, longer DID) and multi-frame TX (long DID Write payload), with correct FC direction and respect for BS/STmin; no unsupported fake success.
- Full payload length validation and bounded receive buffers; errors for malformed DLC/length, wrong CF sequence, missing FC, FC overflow, wrong IDs, and incomplete/mismatched reassembly.
- Transaction timeout and ISO-TP N_As/N_Ar/N_Bs/N_Cr or library-equivalent finite protections; no unbounded native blocking.
- Never send ISO-TP Flow Control for unrelated or unsolicited traffic.
- Ignore/filter unrelated CAN traffic for the transaction while retaining it for monitor.

Receive example:

```text
Request UDS: 22 F1 90
TX ID 0x681: 03 22 F1 90 00 00 00 00
RX ID 0x601: 10 14 62 F1 90 4D 47 55
TX ID 0x681: 30 00 00 00 00 00 00 00
RX ID 0x601: 21 56 35 4A 54 4C 58 54
RX ID 0x601: 22 4A 39 39 39 37 34 31
Full UDS response: 62 F1 90 4D 47 55 56 35 4A 54 4C 58 54 4A 39 39 39 37 34 31
```

The example illustrates required behavior, not actual hardware result.

### M04-04 — Small UDS request/response coordinator (NO security)

Take the UDS payload exactly from the row's `DiagnosticStep.request` (parsed as valid bytes), do not prepend ISO-TP PCI bytes; use the resolver's physical CAN IDs.

- Reject empty/invalid request, disconnected service, wrong/ambiguous ECU, unsupported addressing, or busy transaction.
- **Reject every outbound request whose UDS Service ID is `0x27`** with a clear `Security Access is not enabled` UI message; reject without sending any CAN frame. Do not call a configured DLL or perform any automatic security sequence. This applies even when `.diag` has `27 01`/`27 03` steps.
- For nonsecurity, prioritize working `22 F1 90`, `10 03`, `19 ...`, and `3E 00` paths. If other UDS services are accepted, enforce the same transport and error contracts.
- Add an explicit manual confirmation for potentially state-changing services (`11`, `14`, `2E`, `31`, `85`, and other writing/reset/routine operations). Default to bench-safe behavior, never execute such a row accidentally or through import. **Do not send service `0x27` even with confirmation.**
- Distinguish positive response from a properly structured negative response `7F <requested SID> <NRC>`.
- NRC `0x78` means ResponsePending: keep waiting under a separate finite P2* window, respecting a maximum total duration and cancellation; do not show Passed or Failed until a final response or explicit timeout. Avoid treating unrelated NRC 0x78 from another SID as belonging to this request.
- Other final NRCs, including security-denied `0x33`, remain transparent negative results (show `7F ...`, map `Failed` with detail/NRC, no automatic unlock).
- Set **application-level defaults** for P2/P2* and total timeout, configurable in a typed object and documented; do not treat `.diag.DelayTime` as a receive timeout. Delay and Repeat are metadata for a future sequence runner. For now one `>` click means exactly **one** request; no implicit `RepeatTimes` or `DelayTime` loops.
- Prevent reentrancy/race: one active request globally on the selected CAN interface until completion or cancellation.

Expected-response evaluation:

- Use `DiagnosticStep.match`: `prefix`, `exact`, `wildcard` when safely defined. Reuse any existing normalizer/semantics from the native Diagnostic Sequence repository; do not invent unsupported wildcard syntax. If wildcard syntax is undefined, explicitly reject it with `Not Evaluated`/clear error until implemented and tested.
- Compare **reassembled UDS payload**, NOT CAN PCI bytes; use `62 F1 90` prefix matching by default for imported `.diag`.
- Empty Expected Response → `Not Evaluated`, even on positive response (display actual payload).
- Final negative response → `Failed` and show NRC even if it incidentally matches an expectation prefix, unless explicit negative-expected semantics are separately defined and tested.
- Timeout / transport fault → `Timeout` / `Error`, never `Failed` based solely on missing response.

### M04-05 — Wire existing UI without redesign

Keep Commit 56 layout, splitter ratios, Save Order, sequence import/export, selected Vehicle, current test case, Light/Dark, scrollbars, buttons and all existing connection controls.

Add a focused `CanDiagnosticController` (or similarly named controller) to handle:

- `CanDiagnosticTablePanel.row_send_requested(step_id)`.
- Freeze source/document generation and row UUID `step_id`; retrieve `step_for_id` and active Vehicle at click time.
- Resolve the exact ECU and build immutable request.
- Submit to owner transport worker without blocking GUI.
- Update `set_step_running(step_id)` and then `set_step_result(step_id, payload, outcome, detail)` **only on GUI thread**, **only if same document/generation and row ID still exist**.
- Never put bus/protocol logic in `can_interface_tab.py` or QTableWidget.
- Disable active-row `>` and other conflicting manual sends while transaction is executing; do not double-submit from rapid clicks.
- Keep `Run Selected` disabled for this milestone; checkbox remains independent of `>`.
- On document reload, Vehicle switch, row edit/delete, close tab or Disconnect: cancel or invalidate in-flight transaction, discard late results and prevent them from marking a different row.
- Keep `CurrentTestCasePanel` read-only; show row/response info if fitting existing fields, do not introduce a second Send button.
- Thread-safe status errors must surface via existing notice/UI and optional small non-modal details, not repeated blocking modal dialogs for each received frame.
- `27 xx` row remains displayed/editable as imported but must be non-executable; show concise reason.

Monitor integration:

- Use existing `CanMonitorPanel.append_frame_batch` on GUI thread to show **actual** CAN frames, including tester TX, ECU RX and ISO-TP FC.
- Bound batches, queue, and memory. Do not rebuild a 2000-row QTableWidget on every single frame during high traffic; throttle rendering at ~50-100 ms as needed without changing existing filter semantics.
- Separate 'Captured during request' from 'Continuous monitoring' if the latter is not implemented. Do not claim live monitoring while the RX owner is inactive.
- Keep Start BLF Log and Export CSV disabled until real writer/exporter is implemented in its own phase. The raw frame bus-event hook must enable future BLFWriter without protocol rewrite.

### M04-06 — Cleanup and hardware error recovery

M02 resource ownership and connection snapshot are authoritative. Do not introduce a second CAN Bus or bypass `owned_vector_bus.py`.

- Disconnect while a transaction is running must trigger cooperative cancellation/stop receive first; then shutdown native bus in the established owner thread; no concurrent `bus.recv()` / `bus.send()` / `bus.shutdown()` across unrelated threads.
- Ensure cancellation is responsive even when the worker is processing a request; design small bounded pump ticks or a thread-safe cancellation event that the actual worker checks. A queued Disconnect cannot execute until a never-returning worker slot finishes; **do not build such a loop**.
- After confirmed cleanup report DISCONNECTED. If cleanup is uncertain, preserve M02 `RECOVERY_REQUIRED` and refuse additional request/connection attempts.
- Classify unplug/driver error based on actual native error, not ordinary ISO-TP silence.
- Handle application/window shutdown with no dangling QThread or leaked Vector handles.
- Do not restart the bus automatically, or silently change CAN channel after transport errors.

## 5. Integration and safety gates

Important edge cases:

- Device discovered but **not connected**: `>` cannot send.
- Connected to a channel with no correctly configured ECU: show configuration error, send nothing.
- A selected Vehicle's `ECU.request_id`/`response_id` fields contain HEX strings (e.g., `681`, `601`); if blank, malformed, equal/ambiguous, or outside supported addressing, reject safely.
- `.diag` embeds different CAN IDs or DLL path: still use current Vehicle's canonical configuration; don't modify the source definition.
- Editing a row while a request is outstanding must not overwrite a different row's result.
- Step expected-response comparison must stay separate from protocol parsing.
- A diagnostic request can be accepted by the CAN driver but ignored by the ECU: timeout, NOT Passed.
- NRC `0x78` handling requires a final answer or bounded timeout.
- No Security Access via any path, including keyboard shortcuts, hidden helper methods, or automated chained requests.
- Do not auto-execute steps when importing a `.diag`.

## 6. Required tests (mock first)

Write new tests, with fake CAN bus and fixture vehicles; avoid depending on Vector hardware in CI:

1. ECU `"681"`/`"601"` parsed as HEX, not decimal; optional `0x` prefix.
2. Vehicle missing / ECU missing / ambiguous / incomplete IDs rejected.
3. `27 01` and `27 03` rejected **before any CAN send** and no DLL load.
4. Invalid HEX UDS payload rejected.
5. Connected state required for sending; `RECOVERY_REQUIRED` blocked.
6. A row `>` emits and routes correct UUID/request, independent of checkbox.
7. Duplicate `>` clicks create at most one transaction.
8. Correct ISO-TP SF encode/decode with optional padding.
9. FF/FC/CF reception produces full 20-byte VIN UDS payload.
10. Multi-frame TX waits for FC and honors BS/STmin.
11. Wrong CAN ID, wrong CF sequence, malformed length, missing FC and FC overflow.
12. Separate unrelated CAN frames do not contaminate ISO-TP but do appear in monitor.
13. `62 F1 90` prefix passes the 20-byte VIN payload.
14. Exact expected-response mode passes/fails appropriately.
15. Empty expected response returns `Not Evaluated` with actual response shown.
16. Final NRC (`7F 22 31`, `7F 2E 33`) returns `Failed` plus NRC detail, no unlock attempt.
17. NRC 0x78 then positive response completes; endless 0x78 times out under max budget.
18. Timeout from no ECU response leaves RX/worker responsive and allows later retry.
19. Driver send error and receive error properly cancel or recover.
20. Disconnect during pending FF/CF or 0x78 cleans resources; no leaked worker.
21. Close tab/application while busy safely stops session.
22. Selection or document change drops stale response (generation guard).
23. Editing/deleting a row does not attribute previous response to another step.
24. Monitor displays true TX and RX direction; no invented successful frames.
25. Queue and display are bounded under high traffic; Disconnect remains responsive.
26. Existing M01/M02/M03 UI and native sequence regression tests still pass.
27. Dark/Light switching doesn't erase genuine runtime response.
28. `Run Selected` stays disabled; BLF/CSV buttons remain disabled.

No fabricated hardware success. Save hardware evidence separately from fake/mock assertions.

## 7. Windows hardware acceptance — separate checklist

On an isolated, properly terminated bench/test vehicle setup with the correct Vector XL Driver:

- Discover and **Connect** selected physical Vector channel; verify actual Connected state, not just a visible channel name.
- Select the intended Vehicle and ECU mapping in Vehicle Manager.
- Choose known-safe `22 F1 90` step for BCM.
- Confirm outgoing 0x681 request and incoming 0x601 response in a trusted CAN trace.
- Confirm FC on 0x681 and correct full VIN reassembly.
- Confirm `Receive Message` shows only `62 F1 90 ...`; `Passed` uses prefix comparison, not a made-up result.
- Test a single-frame safe request with known expected answer, then an appropriate multi-frame request on bench.
- Test timeout with missing ECU, disconnect during waiting, reconnect after clean close.
- Verify `27 01` displays disabled/not supported and emits **no frames**.
- Verify monitor directions and timestamps against an external capture.
- Test Light/Dark, 1366×768 and 1600×900, and re-open the app after clean Disconnect.

Never test destructive operations on a production vehicle or assume that a CAN channel being discovered is enough to transmit.

## 8. Deliverables and documentation

Suggested organization (adapt only after reviewing actual code):

```text
core/diagnostic_request.py              # request/result value objects
core/isotp_settings.py                  # configuration/limits, if useful
services/can/ecu_diagnostic_resolver.py # Vehicle -> CAN IDs, pure
services/can/isotp_transport.py         # ISO-TP engine/adapter, pure/testable
services/can/diagnostic_client.py       # single request, NRC/P2/P2* policy
services/can/can_service.py             # safe extension of owner APIs
services/can/vector_backend.py         # small controlled send/receive adapters
 gui/controllers/can_diagnostic_controller.py  # per-row UI coordination
 gui/workers/can_connection_worker.py   # extend original owner, no 2nd Bus
 gui/widgets/can_interface/diagnostic_table_panel.py # action state and runtime rendering
 gui/widgets/can_interface/can_monitor_panel.py      # batch real CAN frames
 tests/services/test_isotp_transport.py
 tests/services/test_diagnostic_client.py
 tests/gui/test_can_diagnostic_execution.py
 docs/can_interface/M04_UDS_NON_SECURITY_REPORT.md
```

Do not put new modules under `gui` merely to hide transport logic. Keep diagnostic protocol layers UI-independent and mockable. Minimize M02 connection lifecycle changes and preserve backwards-compatible tests.

Write `docs/can_interface/M04_UDS_NON_SECURITY_REPORT.md` describing:

- Actual changed files and rationale.
- Bus/RX thread ownership with an explicit sequence diagram.
- API and exact ECU ID parsing.
- ISO-TP configuration (addressing, padding, BS, STmin, timeouts).
- UDS response and NRC 0x78 logic.
- Security 0x27 block and safety guard for state-changing services.
- Row UUID/source-generation guards and cancellation.
- Monitor frame-capture behavior and BLF deferred.
- Automated tests (commands and real outcomes).
- Hardware tests performed vs unperformed (clearly separate).
- Known limitations and readiness for BLF logging / bulk sequence runner.

**Acceptance:** In a hardware test or verified end-to-end fake bus test, a user clicks `>` on BCM `22 F1 90`, the transport sends valid ISO-TP frames on the *selected bus*, reassembles actual response bytes, shows them in `Receive Message`, and updates `Results` via the expected match rule. All safety/cleanup and M01-M03 regression contracts remain valid.

Suggested commit message: `CAN Interface - M04 Non-Security UDS Communication`.

Do not implement SecurityAccess, Seed-Key DLL or BLF file writing in this milestone.
