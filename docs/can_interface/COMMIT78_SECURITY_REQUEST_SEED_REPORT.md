# Commit 78 - SecurityAccess Request Seed, Milestone 1

## Scope and baseline

Implemented against Commit 77, `19c2024cc888893323ac2757816a01add0f19da7`, following `.codex/skills/vcode-security-seed-request/SKILL.md`.

Only the manual, exact two-byte request `27 01` is newly admitted. This milestone retrieves a seed; it does not calculate a key, send `27 02`, invoke a DLL, unlock an ECU, or automatically select a diagnostic session. No commit or push was performed.

The pre-existing user change to `config/diagnostic_sequences/203.BCM&BasicDID.json` was preserved byte-for-byte. Its SHA-256 before and after is `ebe597bef299cfbcfe7ce94fffbfa62a263a6aab7796f2214cbed4f770286130`. The user-provided untracked skill directory was also preserved.

## Existing implementation reviewed

- `core/diagnostic_request.py`: admission, confirmation policy, positive/negative response correlation and expected-response evaluation.
- `gui/widgets/can_interface/diagnostic_table_panel.py`: HEX validation, ECU resolution, Send enablement, runtime updates and cancellation signals.
- `gui/controllers/can_diagnostic_controller.py`: manual confirmation, request generation, stale-result protection and result display.
- `services/can/ecu_diagnostic_resolver.py`: canonical Vehicle/ECU addressing and request construction.
- `services/can/diagnostic_client.py`, `services/can/isotp_transport.py` and existing CAN owner/diagnostic tests: frame correlation, segmentation, response-pending timing and transport results.
- Existing bench authorization and CAN Monitor/BLF regression tests.

Previously, core admission rejected every SID `27`, while the table separately disabled requests beginning with the string `27`. The positive-response echo map did not contain SecurityAccess. Merely enabling the button would therefore be insufficient and would not enforce a nonempty seed.

## Implementation and safety policy

### Core admission and authorization

`SECURITY_SEED_REQUESTS` contains only `b'\x27\x01'`. `DiagnosticRequest.__post_init__()` allows that exact payload and rejects all other `27` payloads, including extra bytes, `27 02`, `27 03` and `27 81`.

`requires_confirmation` includes this narrow exception. The existing controller asks for explicit manual confirmation; the existing backend `validate_send_policy()` independently rejects an unconfirmed request. The general `SAFE_SERVICES`, `CONFIRM_SERVICES` and `TRUSTED_BENCH_PAYLOADS` sets are unchanged. An existing connection-scoped bench grant cannot authorize `27 01` or bypass its manual confirmation. Other service policies, including programming-session rejection, are unchanged.

Existing configured ECU resolution, physical 11-bit CAN IDs, request length limits, connection generation, busy checks and cancellation remain in place. No automatic `10 03` or repeated seed polling was added.

### Correlation and result semantics

`response_belongs_to_request()` now requires positive SID `67`, exact echo `01`, and at least one seed byte. SecurityAccess does not inherit the suppress-positive-response mask. `67 02`, `67 03`, `67 81` and seedless `67 01` cannot complete this request successfully.

The existing ISO-TP/client path handles SF, FF, FC and CF without modification. Seed length is variable within the existing 4095-byte UDS response limit: tests cover up to 4093 seed bytes. ISO-TP padding is excluded from the UDS payload and cannot turn seedless `67 01` into a valid response. Wrong CAN IDs/echoes are ignored; corrupt framing follows existing transport error handling.

The full valid UDS response is retained in the existing Receive Message field. Existing expectation semantics remain:

| Received response / expectation | Outcome |
| --- | --- |
| `67 01 AB CD`, prefix `67 01` | Passed |
| `67 01 AB CD`, exact `67 01` | Failed |
| Valid seed response, empty expectation | Not evaluated |
| `67 01` without seed | Ignored as a positive completion; times out if no valid response follows |
| `7F 27 XX`, `XX != 78` | Terminal negative / Failed, NRC retained |
| `7F 27 78` | Existing pending state and bounded P2/P2-star/total timing |

Repeated pending responses, elapsed time from the original request, cancellation and late-response protection are retained. A valid seed is diagnostic data, not a claim that the ECU is unlocked. An all-zero, nonempty seed is retained as returned; no unlocking interpretation was introduced.

No extra seed telemetry, analytics or debug logging was added. Only the established operator-requested local diagnostic result/CAN trace displays the response. Existing recording behavior was not changed.

### Table integration

The table parses validated HEX tokens into bytes before applying the allowlist. Existing whitespace normalization works, including tabs/newlines and nonbreaking spaces. Invalid HEX, unsupported subfunctions, missing/ambiguous ECU configuration, disconnected state and busy state keep Send disabled. The signal handler repeats payload and ECU checks, and the backend remains the authoritative admission boundary.

No layout, editor/save behavior, sequence JSON, Vehicle Manager, DLL provider, native Vector ownership, continuous capture or BLF implementation was changed.

## Changed files and functions

| File | Change |
| --- | --- |
| `core/diagnostic_request.py` | Seed allowlist; `DiagnosticRequest.__post_init__`, `requires_confirmation`, `response_belongs_to_request` |
| `gui/widgets/can_interface/diagnostic_table_panel.py` | `_request_step`, `_set_button_state`, new `_request_payload` helper and scoped tooltips |
| `tests/services/test_security_seed_request.py` | Nine new policy, correlation and mock transport test methods |
| `tests/gui/test_security_seed_request.py` | Four new end-to-end mock CAN/Qt test methods |
| `tests/services/test_ecu_diagnostic_resolver.py` | Replace old blanket `27 01` denial expectation with unsupported `27` variants |
| `tests/services/test_bench_connection_policy.py` | Seed remains outside connection authorization; unsupported variants still rejected |
| `tests/services/test_trusted_bench_session.py` | Same authorization boundary regression |
| `tests/gui/test_can_diagnostic_execution.py` | Preserve rejection tests for unsupported SecurityAccess payloads |
| `tests/gui/test_vehicle_dll_integration.py` | Existing read-only DLL/theme test uses still-forbidden `27 02` |
| `docs/can_interface/COMMIT78_SECURITY_REQUEST_SEED_REPORT.md` | This report |

The controller, resolver, transport, CAN service, DLL/provider implementation and configuration files required no source changes.

## Validation

New core tests were first run against the blanket-denial implementation and failed at seed request construction. After the patch, all new seed tests pass. Existing diagnostic/transport/policy checks also passed in the targeted 41-test run; that overlapping run is not added to the aggregate below.

The local QA runner at `output/qa_commit78/run_validation.py` isolates UI preferences in temporary directories under the workspace and disables inspection of external DLL references. Mock DLL fixtures remain supported. It does not execute production DLLs or use Vector hardware. QA scripts/results/screenshots are ignored local artifacts, not product changes.

Commands executed from the workspace in offscreen Qt mode:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe output/qa_commit78/run_validation.py seed
.\.venv\Scripts\python.exe output/qa_commit78/run_validation.py can
.\.venv\Scripts\python.exe output/qa_commit78/run_validation.py m5b
.\.venv\Scripts\python.exe output/qa_commit78/run_validation.py commit64
.\.venv\Scripts\python.exe output/qa_commit78/run_validation.py log
.\.venv\Scripts\python.exe output/qa_commit78/run_validation.py can --baseline
.\.venv\Scripts\python.exe output/qa_commit78/run_validation.py commit64 --baseline
.\.venv\Scripts\python.exe output/qa_commit78/render_seed.py
```

| Group | Run | Passed | Assertion failures | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: | ---: |
| New seed policy/transport and GUI | 13 | 13 | 0 | 0 | 0 |
| CAN M01-M04B, connection/owner, ISO-TP, diagnostic client/UI, bench policy, monitor/BLF, ASC/BLF pipeline | 254 | 243 | 9 | 2 | 0 |
| M05B DLL metadata/storage/mock provider | 36 | 36 | 0 | 0 | 0 |
| Legacy Commit 64 sequence/editor tests | 17 | 9 | 8 | 0 | 0 |
| Log pending matching and DSA-TXT pipeline | 27 | 27 | 0 | 0 | 0 |
| **Aggregate, excluding overlapping targeted/baseline reruns** | **347** | **328** | **17** | **2** | **0** |

The broader regression suite is **not all green**. Baseline comparison loaded the original HEAD versions of both edited product modules and the five updated existing test modules into memory, without resetting the worktree. Under the same QA isolation, baseline CAN was also 254 tests with 9 failures and 2 errors; baseline legacy editor was also 17 tests with 8 failures. Test counts and the complete problem-name sets are identical before and after: no added failures in these compared groups.

Existing baseline problems concern newer editor/import behavior versus older test expectations: tooltip wording, external sequence inventory/restore, order/import expectations, autosave versus Cancel/discard, blank new rows/sequence names, raw HEX preservation and strict type handling, ECU display/selection, and the old five-button footer/draft persistence model. They were left outside this milestone. The two baseline errors are `test_sidebar_cancel_keeps_unsaved_document_active_without_selected_signal` and `test_added_row_hidden_sequence_name_remains_native_saveable`.

Seed coverage includes exact-only admission; nonempty variable-length SF/MF seeds; maximum existing payload; prefix/exact/empty expectations; wrong echo/SID/CAN ID; malformed SF/CF; padding; terminal NRCs `7F`, `22`, `24`, `33`, `35`, `36`, `37`; repeated `78`, delayed final response and pending timeout; unrelated negative responses; explicit confirmation and rejection; no auto session/key/DLL; unresolved ECU/disconnect; edit cancellation and late responses; owner-thread preservation, unrelated monitor traffic and Light/Dark refresh.

All nine changed/new Python files passed syntax compilation. `git diff --check` passed for the patch. Configuration hash verification passed. Independent read-only review found no new correctness/authorization/false-Pass issue; it also passed the 13 seed tests and six aggregate in-memory checks, including rejection of all 65,536 three-byte `27` variants and comparison of other service policies with baseline.

Light and Dark offscreen screenshots were generated and visually inspected: both show complete `67 01 AB CD`, Passed under prefix expectation, and actual mock TX/RX entries in the unchanged monitor layout. These are mock acceptance images, not evidence of physical ECU communication.

## Manual hardware acceptance checklist

Hardware acceptance remains to be performed by the operator on an explicitly authorized test bench:

1. Select the intended Vector device/channel and confirm the Vehicle/ECU physical request and response CAN IDs. Connect.
2. If that ECU requires a session, manually send the appropriate session request such as `10 03` and inspect its real response. The application does not send it automatically.
3. Enter request `27 01`, expectation `67 01`, and prefix matching. Click the row `>` and accept the manual confirmation.
4. Inspect the complete `67 01 <seed...>` in Receive Message and the request/response/FC frames in CAN Monitor. Inspect NRC feedback if the ECU rejects the request or remains pending.
5. Verify no `27 02`, key calculation or DLL execution occurs. Do not interpret Passed as ECU unlock.
6. Repeat with SF/MF ECU responses where available, disconnect/reconnect, and check that cancelled/old requests cannot update a newer row.

## Remaining limitations

- No live Vector/ECU or production DLL was used. Physical timing, ECU-specific session requirements and hardware acceptance are unverified.
- A seedless/wrong-echo response is ignored by the existing correlation path, so the operator may see Timeout rather than a dedicated malformed-seed status.
- Existing transport limits/timing remain unchanged. This milestone adds no other SecurityAccess level, key submission, automatic retry, session switching or unlock workflow.
- The 19 pre-existing baseline test problems above remain; the complete regression suite cannot be reported as passing.
