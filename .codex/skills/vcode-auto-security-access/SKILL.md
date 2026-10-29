---
name: vcode-auto-security-access
description: Implement one-action, end-to-end UDS SecurityAccess Level 1 in the existing V-CODE CAN Interface: 27 01 -> 67 01 + Seed -> verified Key -> 27 02 + Key -> exact ECU 67 02, with a composite test result, strict authorization, and no unsupported real-DLL activation.
---

# V-CODE — One-Action Auto SecurityAccess (Commit 83 feature)

## Mission

Implement the user's final desired behavior in `dathp95/UDS-Analysis`: a test-sequence row configured with **Request `27 01`** and **Expected Response `67 02`** is executed with **one press of `>`**. V-CODE internally runs two **distinct** UDS transactions and shows the ECU's final `67 02` on that same row only when the ECU actually accepts the generated Key.

```
User: row Request = 27 01, Expected = 67 02; press > ONCE
  [preflight: exact ECU/Vehicle, authorization, current Extended session, provider]
  V-CODE -> ECU: 27 01
  ECU -> V-CODE: 67 01 + 16-byte Seed
  V-CODE: validated, verified Seed-Key provider calculates 16-byte Key
  V-CODE -> ECU: 27 02 + Key    [separate UDS transaction, same CAN owner]
  ECU -> V-CODE: 67 02         [exact positive UDS payload]
  Sequence row: Receive = 67 02, Result = PASSED
```

**Critical distinction:** `67 02` is **NOT** a direct response to `27 01`; do not modify UDS correlation to pretend that it is. One row in the sequence may contain two transport-level requests, managed by a higher-level orchestration state machine.

## Verified baseline and references

- Latest examined HEAD: Commit 82 `4aaa19be4bdf3071a36afead34775e6e7965654a` (re-check actual HEAD before changes).
- Commit 82 already has: `SecurityAccessSession`, `SecurityKeyJob`, `SecurityKeySubmission`/`SubmissionAuthority`, `ProviderVerificationGate`, `SimulatedCANBackend`, an `Unlock L1` UI action, owner-thread ISO-TP transport, and exact `67 02` matching for generated-key requests.
- Existing relevant modules:
  - `gui/controllers/can_diagnostic_controller.py`
  - `gui/widgets/can_interface/diagnostic_table_panel.py`
  - `gui/widgets/can_interface/current_test_case_panel.py`
  - `gui/workers/can_diagnostic_session.py`
  - `services/can/can_service.py`
  - `services/can/security_access_session.py`
  - `services/can/hmac_sha1_provider.py`
  - `services/can/simulated_backend.py`
  - `services/can/security_key_service.py`
  - `services/can/security_provider_gate.py`
  - `services/can/seed_key_worker.py`
  - `core/diagnostic_request.py`
  - `core/security_submission.py`
  - `tools/security_worker/SeedKeyWorker.cs`
  - `docs/can_interface/COMMIT82_SECURITY_ACCESS_REPORT.md`
  - `docs/can_interface/VECTOR_SECURITY_ACCESS_SPEC.md`
- User-supplied `seed_key.txt` describes a desired Python `udsoncan` + `GenerateKeyEx` design, **not** proof of native ABI. Retain V-CODE's existing **Vector CAN owner/ISO-TP** rather than introducing PCAN or a second UDS receiver.
- OEM Security Access spec describes 16-byte Seed, 16-byte Key, 8-byte per-level OEM secret, HMAC-SHA1 truncated to the first 16 bytes **for that profile**. Do not assume BCM.dll matches that profile without offline proof.
- Vector `AN-IDG-1-017` documents the general GenerateKeyEx / GenerateKeyExOpt contracts, not the exact calling convention, ABI or proprietary parameters of the project's BCM.dll.
- Commit 82 report explicitly says **no OEM DLL was executed**, **no native reference vector was compared**, and **no physical 27 02 was transmitted**. Do not conflate simulator PASS with OEM-ECU PASS.

## Hard boundaries (do not weaken)

1. **Do not enable live `27 02` unless a real provider has an independently validated ABI/profile, correct ECU/resource fingerprint, authorized test vectors, trusted provenance, and a currently authorized bench.** If missing, keep physical auto-unlock BLOCKED; implement simulator-complete UX and report the exact blocker.
2. Do **not** infer or guess proprietary OEM keys, calling convention, `iSecurityLevel` mapping, return enum, `ipVariant` encoding, options, buffer sizes or magic DLL inputs. Do not brute force keys or use a live ECU as an algorithm oracle.
3. No arbitrary/manual `27 02` entry in the grid, config import, or generic `DiagnosticRequest`. Only the one-use generated-key capability can admit a key send.
4. No automatic retries after negative response (especially NRC 35, 36, 37), no automatic escalation from L1 to L2+, no hidden session changes, no silent sending on row selection or import.
5. No parallel CAN transport, no new CAN worker, no second `udsoncan.Client` consuming the same RX queue. You may use `udsoncan` in isolated protocol tests only.
6. Use **real ECU response `67 02`** as the sole positive proof of a completed key transaction; driver TX success, DLL return success, computed key length, or `67 01` alone cannot mark the row PASSED.
7. Do not hardcode CAN IDs; use Vehicle Manager ECU mapping. Protect Seed/Key, secrets, vendor DLLs, reference vectors and proprietary PDFs from Git, logs, Monitor, CSV, BLF, reports, exception traces and debug output. Preserve or improve the existing key-frame redaction.
8. Keep existing manual `27 01` seed-only functionality, unrelated UDS commands, CAN Monitor, BLF, Log Analyzer, GUI themes and sequence editing unchanged.
9. Never claim hardware success without an authorized physical test and captured ECU confirmation. Do not commit or push changes unless explicitly directed.

## UX contract: trigger and observable result

- **Auto mode**: a row with `Payload (HEX) = 27 01` and `Expected Response (HEX) = 67 02` opts into *Auto Security Access L1*.
- **Seed-only mode**: a row with `27 01` and expected `67 01` (or blank) retains existing single-request behavior. Preserve import compatibility.
- For Auto mode, show **one logical row** with intermediate states in the existing Result/Comment UI: `Preflight`, `Requesting seed`, `Seed received`, `Calculating key`, `Sending key`, `Waiting for ECU`, then terminal `Passed`/`Failed`/`Timeout`/`Cancelled`/`Error`.
- Keep row **Running** after intermediate `67 01`. Do not compare `67 01` against the row's final Expected `67 02` and prematurely mark Failed.
- On successful final ECU response: `Receive Message (HEX) = 67 02`, `Result = Passed`, `Comment = Security Unlocked (Level 1)` plus safe timing/meta, with *no raw Key*. Intermediate seed response can be retained in a dedicated in-memory trace, not silently substituted for the final response.
- On negative response to seed or key: show original safe NRC/step, Result `Failed`. On transport failure or unverified provider: `Error/Blocked` with reason, not `Passed`. On timeout: `Timeout`.
- The separate `Unlock L1` button from Commit 82 may stay for manual diagnostic use, but must **not** be required for Auto mode.

## Authorization and the one-action requirement

- A physical auto-unlock must require a pre-authorized **specific connected test bench and target ECU**, a verified provider and active Extended session. Authorization is **not** granted by merely setting `Expected = 67 02` in an imported file.
- The operator's deliberate `>` press is the initiation/consent for **one scoped two-transaction workflow**, **only if** an explicit bench authorization for this target and operation was already established. Consume a fresh one-shot capability before key submission. Do not show a second `Unlock L1` dialog when that pre-authorization is satisfied; do not bypass existing authorization by adding a Boolean flag to JSON/env.
- If current application policy demands a second per-key confirmation and cannot safely reuse a pre-authorized one-shot workflow grant, **keep that confirmation** and document that strict one-click UX is blocked pending an approved authorization design. Never silently remove the existing security gate.
- Preflight should fail safely **before sending `27 01`** when known prerequisites are absent. Extended session `10 03` must already be confirmed for the same ECU, or be an explicitly configured, authorized prerequisite; never silently change diagnostic session.

## Implementation milestones

### M1 — Audit and baseline

1. Check HEAD, inspect Commit 82 source and focused tests; run a reproducible baseline and record existing failures separately.
2. Map the exact call chain from row `>` -> `send_row` -> `resolve_request` -> `task.submit_diagnostic` -> `CanDiagnosticSession` -> `CanService` -> ISO-TP -> `DiagnosticResult` -> `_result`.
3. Map the existing `SecurityAccessSession`, `SecurityKeyJob`, `SubmissionAuthority`, `ProviderVerificationGate` and all connection/session/vehicle/ECU invalidation signals. Detect possible callback ordering and double-click/reentrancy bugs.
4. Identify any real-key leakage in `repr()`, generic logs, error notices, export/capture and UI.

### M2 — A composite one-row orchestrator

1. Add a testable stateful `AutoSecurityAccessL1` coordinator (recommended location: `services/can/auto_security_access.py`, with a thin Qt controller adapter). It owns *one logical sequence result* and dispatches *two existing physical UDS requests*.
2. Detect Auto mode **only** for the exact user row (`27 01`, Expected `67 02`); persist its original row/step/transaction/document identities and original Expected for final presentation.
3. Perform target-specific preflight (connected CAN, bench, Extended session if required, profile, current provider, vehicle/ECU, TX/RX, document generation). No on-wire request if required prerequisites are knowingly missing.
4. Create the **seed subrequest** (`27 01`, expected `67 01` prefix), and let the normal protocol matcher correlate only its `67 01 + 16-byte Seed` response. Keep the logical sequence row Running.
5. Deliver received seed to `SecurityAccessSession`; reject malformed/empty/wrong-subfunction/expired seed. Handle all-zero 16-byte seed as *already unlocked* according to the verified ECU profile, without sending Key; label status distinctly from a newly completed `27 02/67 02` transaction, and **do not fabricate `67 02`**.
6. Dispatch async verified-provider calculation via existing `SecurityKeyJob`. Bind the result to the exact Seed transaction, resource fingerprint, CAN connection generation and ECU/security-session epoch. Any context change cancels and clears material.
7. After calculation, issue **one** scoped `SecurityKeySubmission` using the existing `SubmissionAuthority` and CAN owner, with the one-workflow authorization conditions above; use `27 02 + 16-byte Key` via the unchanged ISO-TP pipeline.
8. Require an exact correlated positive `67 02` from the same ECU RX/transaction to complete. Report it as the **final logical row result**. Preserve 2 physical transaction records internally for diagnostics.
9. Ensure that while the chain is active, unrelated row sends cannot race with the sequence; worker calculations must not block Qt GUI or CAN owner. Cleanup must work on close/disconnect/cancel/ECU or Vehicle switch.
10. Carefully handle the handoff between the first and second transactions so `_active`, `diagnostic_busy`, one-shot capability and row UI are not prematurely cleared or overwritten. Keep intermediate progress separate from terminal `Result`.

### M3 — Real key generator as a separate readiness gate

- Reuse the verified provider path from Commit 82: `services/can/hmac_sha1_provider.py` and `ProviderVerificationGate`. Simulator dummy HMAC may only be used with `SimulatedCANBackend`.
- For a *real* `BCM.dll` provider, inspect a genuine native SDK/header and exact binary, establish calling convention, argument types/indirection, return enum, security-level mapping, `Variant`, buffer/actual-length and library architecture. Run an isolated **x86 subprocess**, not a 64-bit Python `ctypes.CDLL` import. Pin the file SHA-256 and ECU applicability.
- Compare the real provider output byte-for-byte against **all 18 authorized Level 1 BCM reference pairs** cited in the prior report. Reference vectors must remain in a local gitignored fixture. Verification status is BLOCKED unless actual comparisons execute and pass.
- Alternative: an OEM-approved, per-level HMAC secret source may be used **only** with signed/approved ECU applicability and identical offline vector verification. Never derive a real secret from sample seed/key traffic or commit secrets.
- Do not reuse the simulator's static dummy key as `verified_real=True`; never treat successful mock tests or a non-null DLL path as a real provider.
- Keep physical auto-send disabled unless real-provider readiness is verified **in the running process** for the exact ECU/DLL resource.

### M4 — Acceptance rules and failures

| Event | Logical row outcome | Subsequent transmission |
|---|---|---|
| `67 01 + valid nonzero Seed` | Running: seed accepted | Calculate verified Key |
| Provider validated and scoped authorization available | Running: key ready | One `27 02 + Key` send |
| Actual ECU returns exact `67 02` for current key request | **Passed** | No additional send |
| `7F 27 78` | Running / response pending under P2* | No duplicate request |
| `7F 27 24`, `33`, `35`, `36`, `37` | Failed with matching NRC | No retry |
| Missing/invalid ABI, wrong DLL, wrong secret, no vectors, missing bench | Blocked/Error | No `27 02` (ideally no `27 01` at preflight) |
| Disconnect, ECU/Vehicle/document/session change, cancelled/expired seed | Cancelled/Error | No key TX |
| Unsupported/malformed positive response, timeout | Error/Timeout | No retry |
| Verified profile returns all-zero 16-byte Seed | Already unlocked (special state; never synthesize `67 02`) | No key TX |

### M5 — Tests and regression

Write focused service, controller and GUI tests using the **existing** simulated backend; add regression cases for all of these:

- One click on `27 01` + expected `67 02` completes exactly two distinct physical UDS transactions in simulator and sets **one** logical row to `Receive=67 02`, `Passed`.
- `27 01` + expected `67 01` / blank retains seed-only semantics; non-security rows unaffected.
- The intermediate `67 01` does not cause an expectation mismatch against final `67 02`.
- Wrong `67 01` subfunction/length, all-zero Seed, malformed `67 02`, wrong ECU Rx, stale queued frame, duplicated callback, worker timeout, provider mismatch and late key calculation are handled without false success.
- NRC `24`, `33`, `35`, `36`, `37`, `78`; response pending followed by final positive or timeout; **no retry** on invalid key or lockout.
- Missing real provider or unverified ABI/profile: physical path refuses to send, including cases when a mock provider is present or `verified_real` is forged.
- One-time authorization: unapproved bench, expired grant, changed session, changed TX/RX, changed Vehicle/ECU, reconnect, cancel, double-click, reentrant result, and reused token are all rejected.
- Check that raw Key and OEM secrets never appear in generic Monitor/BLF/CSV/log/report/UI, even on delayed driver echo or Python exception. No full proprietary Seed/Key pairs in committed fixtures.
- Run focused suite plus established regression: CAN discovery, monitor, BLF, ISO-TP multi-frame, diagnostic grid, sequence reload, themes, Log Analyzer and license. Compare results to actual baseline; never claim previously failing tests are passing.

### M6 — Report and rollout

- Create `docs/can_interface/AUTO_SECURITY_ACCESS_REPORT.md`: commit SHA, changed files, status by milestone, focused/regression command and exact results, simulator transcript with **redacted Key**, live readiness and each blocker.
- Record the two separate statuses explicitly: `Simulator AUTO 27 01 -> 67 02 = PASS/BLOCKED` and `Physical BCM AUTO 27 01 -> 67 02 = PASS/BLOCKED/NOT TESTED`.
- Flag public-repository hygiene: the Commit 82 diff included many diagnostic sequence JSONs and OEM PDFs. Audit exposure/authorization and do not add or copy proprietary assets into this commit.
- Do not activate a live-provider flag because tests pass in simulation. If the OEM DLL ABI/vector gate is not satisfied, finish and commit-ready **simulator code only**, with real CAN key submission blocked.

## Suggested test commands (adapt to actual files)

```powershell
.venv\Scripts\python.exe -m unittest tests.services.test_security_access82 tests.gui.test_security_access82 tests.services.test_security_access_session tests.gui.test_security_access_session -v
.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

## Output required from Codex

1. Implement code (not just a plan), with source locations and concise architecture explanation.
2. Evidence for exactly one visible user click, two internal UDS transactions and one final row PASS/FAIL.
3. Actual test counts, failures and regressions (distinguish baseline from new regressions).
4. Native-provider/ABI and authorized offline-vector evidence, or **precise BLOCKED reason**; never claim a real BCM `67 02` without physical ECU verification.
5. Instructions for testing simulator vs physical bench; no unsafe "force enable" flags and no auto-unlock of unrelated ECUs.
