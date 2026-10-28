# Commit 81 - SecurityAccess Level 1 foundation and release blockers

Date: 2026-10-28 (Asia/Bangkok). Baseline: Commit 80,
`58ff2ed8c994ece126e00e9a010e16462d8bf74e`.

The requested `.agents/skills/vcode-security-access-commit81/SKILL.md` is absent.
The matching project skill in `.codex/skills/vcode-security-access-commit81/SKILL.md`
was used. No commit or push was performed.

**This is a blocked-release foundation, not a completed live unlock feature.**
The x86 mock worker, offline reference analysis, expiring seed lifecycle and closed
submission guard are implemented. Native `GenerateKeyEx` invocation and live
`27 02` remain unavailable because neither supplied C# fragment verifies the ABI.

## Milestones A-E

| Milestone | Implemented and verified | Blocker / remaining work |
| --- | --- | --- |
| A - Audit | Reviewed current core/GUI 27xx gates, controller, resolver, seed parser, mock key service/provider, bench policy and owner transport. Ran pre-edit CAN baseline: 254 tests, 243 pass, 9 failures, 2 errors. Preserved newer Commit 79/80 behavior. | Existing editor/import assertions remain out of scope. |
| B - References | Read the actual workbook with openpyxl; matched complete chronological same-ECU/session exchanges. Found 18 BCM L1 and 18 BCM L2 exchanges; each has 16-byte seed and key. Stored private vectors only under ignored `output/`. Six synthetic extraction tests pass. | **Zero native vectors compared.** These observations do not validate the DLL algorithm or ABI; L2 is reference analysis only, never enabled for sending. |
| C - DLL/process boundary | Reused `VehicleService.resolve_ecu_dll_resource`; inspected x86/export metadata and SHA-256. Built and executed a separate x86 .NET mock worker, verified runtime pointer width 32. Added bounded IPC, cancellation/deadline/crash handling and process-tree cleanup. Nine worker tests pass. | Native adapter deliberately absent. Calling convention, string ABI, return enum and security-level mapping need trustworthy confirmation, followed by real offline vector comparison. |
| D - Session/guard | Added identity-bound, expiring seed session, explicit offline-mock calculation API, safe notices and Light/Dark status. Invalidate on document/Vehicle/ECU/address/session/connection changes, cancellation, expiry and failed seed results. Reject all submission attempts, including confirmed mocks. Nine service/session and six GUI tests pass. | No live key request type is admitted; no KEY_SUBMITTED/UNLOCKED transition or authorized Ready status is reachable. Real guarded submission and exact `67 02` completion path must be added only after C passes. |
| E - Verification | 30 new tests pass; existing seed, key service, DLL/provider, CAN/UDS/BLF and Log Analyzer groups were run. Independent review findings were reproduced and fixed. Syntax, diff, ignored-fixture and original-file checks pass. | Complete suite still has 19 baseline problems. No OEM execution or physical bench test. A successful simulated/live generated-key exchange is not claimed. |

## A: Source audit and preserved policy

`core/diagnostic_request.py` still admits only the exact two-byte `27 01` for
SecurityAccess. Manual key rows such as `27 02 <key>`, additional seed bytes and
other levels remain denied independently in the table and core. The
`SECURITY_SEED_REQUESTS`, safe/confirmation service sets and connection bench
authorization policy were not broadened.

The existing owner-thread CAN/ISO-TP pipeline continues to transmit manual rows.
No bus, RX consumer, polling loop, SecurityAccess retry, automatic session change
or automatic key calculation was added. SF/FF/FC/CF processing, pending NRC 78,
continuous CAN Monitor, BLF, manual diagnostic results and sequence persistence
retain their established paths.

`SecurityKeyService` remains mock-only. Its boundary now validates request bounds,
response type, correlation ID, exact output length and `mock_only is True`, and
forwards cancellation to the provider. A provider claiming to be real is rejected.

## B: Offline reference evidence

Source: `output/Report_LogAnalyzer/28-10-2026/EEIV_LogAnalyzer_Report_VF5NP_20261028_170829.xlsx`,
`ALL_ECUS` sheet, headers at row 2.

Workbook SHA-256:
`62f486c0d3e741d3078a8681540709da2b353661698e1eaf8c91fa5feaa9bddd`.

The parser uses each row's complete Request/Response and numeric Time + RT to
pair seed completion before key submission. It rejects backwards chronology,
intervening same-ECU requests/session changes, wrong echo, seedless positives,
negative/pending seed results and key acknowledgements containing extra data.
Another ECU's traffic cannot consume the candidate, and a seed candidate is used
only once. It does not infer a security level from descriptions or assume a
fixed 16-byte provider output.

| ECU | Odd request subfunction | Complete exchanges | Seed bytes | Key bytes |
| --- | ---: | ---: | ---: | ---: |
| BCM | 01 | 18 | 16 | 16 |
| BCM | 03 | 18 | 16 | 16 |

These exchanges contain 72 positive transaction rows, no negative/pending rows
and no unmatched seed/key in the analyzed workbook. Repeated values remain
separate chronological exchanges; the count is not a count of unique seeds.

Private vectors are in `output/qa_commit81/reference-vectors.private.json`;
`git check-ignore` confirms exclusion. No actual seed/key bytes are included in
tracked source, this report, command arguments or extra telemetry. Shared audit
output contains counts, lengths and hashes only.

## C: Exact DLL and missing ABI evidence

The canonical saved VF5NP/BCM resource resolves to
`config/vehicles/VF5NP/resources/dll/BCM/BCM.dll`:

- Size: 857,600 bytes; architecture: x86 / 32-bit.
- Export `GenerateKeyEx` is present according to static metadata.
- SHA-256: `412b4e91bcf7aa7804cda0de6d83ea13a3425810c3507ba78f6dab031a2150da`.

`inspect_security_provider()` distinguishes missing/invalid resources, unsupported
architecture, missing export, digest mismatch and unverified ABI. It does not
reinterpret an x86 resource as unusable merely because the GUI is 64-bit. Metadata
availability and a matching hash do not authorize DLL execution. Its
`live_enabled` property is always false in this release; no environment/config
toggle can replace verification.

Both user-provided fragments were reviewed:

- `HandleDLL.cs`: seven-argument `GenerateKeyEx` declaration, but no explicit
  calling-convention/string-marshalling evidence for that delegate. The separate
  eight-argument `GenerateKeyExOpt` Cdecl annotation cannot prove the first ABI.
  `CalulateKey()` has an unrecovered/invalid method body.
- `gen.txt`: confirms removing the two response header bytes, calling
  `CalulateKey(seed, odd_subfunction, ref key)` and then constructing the next
  subfunction. It does not reveal how that wrapper maps its arguments to native
  `GenerateKeyEx`. Its initial 16-byte array is not a vendor output-size contract.

Required evidence remains: exact native declaration/header or equivalent verified
specification, calling convention, variant character encoding and pointer
indirection, output buffer/actual-length contract, return enum meanings and mapping
to `iSecurityLevel`. No convention, variant value or mapping was guessed, and no
live ECU was used as an algorithm oracle. `GenerateKeyEx` has **not been called**;
0/18 L1 exchanges have native key comparisons, with no pass claim.

### Worker contract and build

`tools/security_worker/SeedKeyWorker.cs` is explicitly mock-only. It contains no
OEM loader, native delegate, key-request sender or CAN access. `--native` fails
without stdout/stderr. `--probe` reports 32-bit process width, mock-only mode and
native-disabled state. Compiled executable stays in ignored
`build/security_worker/SeedKeyWorker.x86.exe`.

IPC reuses existing typed SeedKeyRequest/Response version 1: four-byte
little-endian length followed by at most 4096 bytes of JSON. Request identity,
fields/types, duplicate members, seed/output bounds (1-64 bytes), response
correlation and exact key length are checked. Secrets travel only in anonymous
pipes, never command arguments or worker temp files. Worker stderr is discarded;
errors have fixed nonsecret codes/text.

The process adapter is one operation at a time. Deadline/cancel/crash paths reap
the worker. On Windows it starts suspended, attaches to a non-breakaway Job Object
with kill-on-close, then resumes its owned main thread. This prevents children
escaping cleanup before job assignment. Closing the job kills descendants that
hold inherited pipes. Reader cleanup is bounded and operation locks are released
even if cleanup fails; cleanup failure cannot return a successful key. POSIX uses
a separate process group for the equivalent test transport.

The built worker was exercised with 1-, 16- and 64-byte mock outputs and matches
the existing deterministic test provider. This validates IPC/process behavior,
**not OEM GenerateKeyEx**. .NET strings/Python immutable copies cannot promise
forensic zeroization; the code removes owned references and bounds session lifetime.

## D: Session lifecycle and UI

Identity includes selected Vehicle/ECU, physical TX/RX IDs, odd subfunction,
transaction/step ID, document generation, capture connection identity and local
diagnostic-session epoch. Request lifetime follows the existing transaction total
budget; received seed/key lifetime is at most 30 seconds, without renewal from
offline calculation. A GUI QTimer expires material without requiring a click.

Implemented transitions: IDLE -> SEED_REQUESTED -> SEED_RECEIVED, optional explicit
KEY_CALCULATED (offline mock), and FAILED/CANCELLED. KEY_SUBMITTED/UNLOCKED are
reserved states with no reachable transition in this gated release. There is no
production UI action that calls the blocking offline provider API; it is an
explicit service/test API to be run outside the GUI thread. Seed reception does
not start a worker automatically.

Context invalidation includes immediate Connect/Disconnect start, capture-ID
change, document/Vehicle/configuration/resource change, selected ECU change,
clicking Send for another ECU even without changing row selection, manual SID 10,
timeout, cancellation and failed/malformed seed response. Late provider/diagnostic
results cannot resurrect cancelled material. Discovery-only service adapters can
still display the tab; an absent capture ID cannot create a SecurityAccess session.

The Current Test Case uses the existing theme-aware label and exposes only state,
including `Seed received` or `Key calculated (offline mock)` and
`27 02 disabled: DLL ABI/offline verification pending`. It never displays a raw
key or an Unlock successful/Ready message. Existing local Receive Message still
shows the operator-requested seed response. Every `prepare_submission()` call is
rejected; neither `authorized=True`, manual confirmation nor a mock/claimed-real
result can bypass core admission. A live key request type/owner-send authorization
path is intentionally not fabricated before ABI/vector validation.

## E: Test commands and results

Commands run from `C:\REDO\CODINGTOOL`:

```powershell
& ./tools/security_worker/build.ps1
.\.venv\Scripts\python.exe -m unittest tests.services.test_security_reference tests.services.test_seed_key_worker tests.services.test_security_access_session tests.gui.test_security_access_session -v
.\.venv\Scripts\python.exe tools/security_worker/analyze_reference.py output/Report_LogAnalyzer/28-10-2026/EEIV_LogAnalyzer_Report_VF5NP_20261028_170829.xlsx --vehicle VF5NP --ecu BCM --local-fixture output/qa_commit81/reference-vectors.private.json
$env:QT_QPA_PLATFORM='offscreen'
# Isolated local runner: temp UI stores, synthetic DLL tests only.
.\.venv\Scripts\python.exe output/qa_commit81/run_validation.py new81
.\.venv\Scripts\python.exe output/qa_commit81/run_validation.py key80
.\.venv\Scripts\python.exe output/qa_commit81/run_validation.py seed
.\.venv\Scripts\python.exe output/qa_commit81/run_validation.py can
.\.venv\Scripts\python.exe output/qa_commit81/run_validation.py m5b
.\.venv\Scripts\python.exe output/qa_commit81/run_validation.py log
.\.venv\Scripts\python.exe output/qa_commit81/run_validation.py commit64
.\.venv\Scripts\python.exe output/qa_commit81/run_validation.py commit64 --baseline
```

| Group | Run | Pass | Failures | Errors | Skip |
| --- | ---: | ---: | ---: | ---: | ---: |
| New Commit 81: reference 6 + worker 9 + service/gate 9 + GUI 6 | 30 | 30 | 0 | 0 | 0 |
| Existing Commit 80 key service | 5 | 5 | 0 | 0 | 0 |
| Existing seed policy/transport/GUI | 13 | 13 | 0 | 0 | 0 |
| CAN M01-M04B/bench/ISO-TP/diagnostics/monitor/BLF and ASC/BLF pipeline | 254 | 243 | 9 | 2 | 0 |
| DLL resource/storage/mock provider | 36 | 36 | 0 | 0 | 0 |
| Log pending matching and DSA-TXT pipeline | 27 | 27 | 0 | 0 | 0 |
| Legacy Commit 64 codec/editor tests | 17 | 9 | 8 | 0 | 0 |
| **Aggregate (excludes overlapping focused and baseline reruns)** | **382** | **363** | **17** | **2** | **0** |

CAN pre-edit baseline has the same 9 failures/2 errors; original-HEAD legacy editor
comparison has the same 8 failures. Both full problem-name sets and test counts
match final results, with no added problems. The entire suite is **not green**.
Existing problems concern old editor/import/ECU-display/footer/order/autosave and
tooltip expectations; they were not hidden by changing those tests.

RED/GREEN evidence includes absent new modules/session UI before implementation,
then lifecycle corner cases before fixes. Independent review reproduced two P2
issues: seed still usable at disconnect start, and a child holding stdout causing
cleanup to exceed timeout. Both were fixed with regression tests. The local
descendant repro took 3.266 seconds for a 0.2-second deadline before the fix;
afterwards it passes the under-2-second bound including cleanup. Independent
re-review measured 0.218 seconds for a 0.2-second deadline, with no remaining
pipe thread, and passed 14 worker/GUI checks. Both findings were closed. The
before/after attach failure repros were added to the permanent suite as well.
A discovered
discovery-only adapter initialization regression was also fixed and rerun.

Syntax compilation covers all 14 changed/new Python files; whitespace/diff and
private-fixture ignore checks pass. Light/Dark offscreen screenshots were visually
inspected at 1366x768: full mock seed response, existing table/monitor layout,
and readable disabled-submission status. No actual OEM DLL or CAN hardware was used.

## Modified files

- `gui/controllers/can_diagnostic_controller.py`: seed lifecycle, identity/epoch invalidation, timer/status signal; existing row confirmation/transport retained.
- `gui/tabs/can_interface_tab.py`: connect status to the current-test-case view.
- `gui/widgets/can_interface/current_test_case_panel.py`: accessible plain-text theme-aware status label.
- `services/can/security_key_service.py`: typed/bounded mock result validation and cancellation forwarding.
- `services/can/security_access_session.py`: expiring session, mock calculation and closed submission guard.
- `services/can/security_provider_gate.py`: canonical DLL eligibility/hash, always-closed release gate.
- `services/can/security_reference.py`: secret-safe chronological workbook extraction.
- `services/can/seed_key_worker.py`: bounded one-shot pipe adapter and mock process provider.
- `services/can/windows_worker_job.py`: Windows process-tree attachment/resume/cleanup.
- `tools/security_worker/SeedKeyWorker.cs`, `build.ps1`, `analyze_reference.py`: mock x86 source/build and read-only offline audit.
- `tests/services/test_security_reference.py`, `test_seed_key_worker.py`, `test_security_access_session.py`, `tests/gui/test_security_access_session.py`: focused regressions.
- `tasks/plan.md`, `tasks/todo.md`: appended Commit 81 plan and evidence, retaining previous milestones.
- `docs/can_interface/COMMIT81_SECURITY_ACCESS_REPORT.md`: this report.

The pre-existing user JSON change, `HandleDLL.cs`, `gen.txt`, original workbook
and BCM DLL remain byte-for-byte unchanged. No vendor binary/private vectors are
added to Git. Licensing, Vehicle configuration schema, sequence editor/save,
native CAN ownership, BLF implementation and `services/seed_key_provider.py` were
not modified.

## Remaining release gates

1. Recover trustworthy native ABI evidence for the exact pinned DLL; independently
   review convention, string indirection/encoding, enum and level mapping.
2. Implement the real worker adapter only against that verified contract; compare
   every authorized L1 reference key byte-for-byte, stopping on any mismatch.
   Do not count mock results or a return-code success as a vector match.
3. Only then implement a capability-bound key request/owner policy with current
   seed/ECU/session/connection/expiry checks, an explicitly authorized bench and
   confirmation for each live submission. Arbitrary manual key rows must stay denied.
4. Test simulated key submission and exact `67 02` completion plus NRCs, stale
   contexts, cancellation and no retry. Live hardware acceptance needs explicit
   bench permission after these gates pass; it was not performed here.

## Official platform references

- [Microsoft C# platform targeting](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/compiler-options/target-exe-compiler-option): x86 compilation runs the 32-bit CLR; runtime probe separately verifies actual width.
- [Microsoft UnmanagedFunctionPointerAttribute](https://learn.microsoft.com/en-us/dotnet/api/system.runtime.interopservices.unmanagedfunctionpointerattribute?view=netframework-4.8): calling convention and character marshalling are explicit ABI concerns; this does not establish the OEM contract.
- [Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects): non-breakaway child association and kill-on-close cleanup.
- [Microsoft thread handles and identifiers](https://learn.microsoft.com/en-us/windows/win32/procthread/thread-handles-and-identifiers): enumerate/open the suspended worker's own main thread before resume.
