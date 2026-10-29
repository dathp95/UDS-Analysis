---
name: vcode-security-access-commit82
description: Review Commit 81 and implement verified, guarded UDS SecurityAccess Level 1 key generation and ECU 27 02 / 67 02 handling in V-CODE, without weakening existing send policies.
---

# V-CODE — Commit 82: Verified SecurityAccess `27 01 → 27 02 → 67 02`

## Goal and non-negotiable release gate
Base: `dathp95/UDS-Analysis` commit `52aebbb50d8168f4527ace9514f3528fa70695ed` (Commit 81). Build a production-shaped, **bench-authorized** UDS SecurityAccess Level 1 flow. **Implement and test the full flow in a simulated ECU**. Only enable `27 02 + real_key` on a physical ECU when its key generator has been independently verified against official/authorized offline reference vectors, the correct ECU/session is confirmed, and the operator authorizes the individual submission. If not verified: release a working simulator path but keep live key sending blocked. **A mock key must never be submitted to a physical ECU.** Do not claim `67 02` will occur: it can only be returned by the ECU after accepting the key.

## Evidence and implementation rules
Read project source first, don't infer APIs, and preserve Commit 81 behavior. Source audit:
- `core/diagnostic_request.py`: `DiagnosticRequest.__post_init__` only admits exact `27 01`; `validate_send_policy` and `response_belongs_to_request` are also seed-only. Do **not** just add `27 02` to `SECURITY_SEED_REQUESTS` or whitelist all `0x27`.
- `gui/widgets/can_interface/diagnostic_table_panel.py`: manual 27xx row blocking must remain for arbitrary hex payloads.
- `gui/controllers/can_diagnostic_controller.py`: tracks `27 01`, GUI transaction, connection identity, session epoch; currently no automatic key send.
- `services/can/security_access_session.py`: `SEED_REQUESTED/SEED_RECEIVED/KEY_CALCULATED` and reserved `KEY_SUBMITTED/UNLOCKED`; `prepare_submission` intentionally always raises.
- `services/can/security_key_service.py`: currently explicitly rejects `mock_only=False`.
- `services/can/security_provider_gate.py`: `live_enabled=False`, because ABI unverified.
- `tools/security_worker/SeedKeyWorker.cs`: x86 **mock only**, not native DLL caller.
- Reuse `services/can/seed_key_worker.py` and `services/can/windows_worker_job.py`; reuse `VehicleService.resolve_ecu_dll_resource(vehicle,ecu)`, existing CAN owner/ISO-TP transport and bench authorization, never create a competing CAN RX consumer.
- CBT's managed `SendDataMessage` establishes: `27 01 -> 67 01 + seed -> HandleDLL.CalulateKey(seed, odd_subfunction) -> 27 02 + key -> 67 02`, but the native `GenerateKeyEx` calling convention, variant/string indirection and level mapping are **not** proven by `HandleDLL.cs`.
- VinFast `CES_VINFAST_EE_VFDSP50000020_Security_Access_Algorithm_V1.0.3.pdf`: section 3.8/3.9 describes 16-byte seed, per-level 8-byte OEM secret, HMAC-SHA1 truncated to leftmost 16 bytes; 3.3 maps After Sales L1 to `27 01/27 02` in Extended session. The document filename says V1.0.3, page footers V1.0.2; verify applicability to VF5NP/BCM. **Do not treat this PDF as disclosure of the actual OEM secret or evidence the current BCM.dll follows exactly this spec.**
- `udsoncan` separates protocol from `security_algo`: optionally use its SecurityAccess routines in *tests/simulation*; do not install a second connected UDS client or disturb V-CODE transport.

## Milestone A — Baseline and safety audit
1. Record HEAD and test baseline, inspect changed files and `docs/can_interface/COMMIT81_SECURITY_ACCESS_REPORT.md`; preserve the 19 previously reported baseline problems (17 failures / 2 errors) as a separate known list, don't relabel them as passing.
2. Map where manual key payloads are blocked: row widget, `DiagnosticRequest`, policy, response correlation, and owner thread. Enumerate exact required changes and tests before modifying anything.
3. Verify bench authorization state and what signal indicates a new physical connection or diagnostic session. Add no silent authorization or unsafe config/environment override.

## Milestone B — Verified key provider, offline only
Implement a typed `RealSeedKeyProvider` distinct from `MockSeedKeyProvider`; return provenance metadata such as `verified_real`, ECU/vehicle, DLL SHA-256 or HMAC key profile id, algorithm revision, and source seed-transaction identity. `mock_only=False` from an arbitrary provider is **not sufficient** to authorize sending: require trusted provenance/capability issued by a verification gate bound to the current resource and verified vectors.

**Option 1: OEM-approved HMAC profile.** Build `services/can/hmac_sha1_provider.py` using Python standard `hmac` and `hashlib` (16-byte seed, 8-byte level-specific OEM key, `digest()[:16]`). Obtain secret only from a genuinely authorized secret source, not hardcoded / committed / debug logged. Validate profile-to-ECU mapping and official expected vectors. Use dummy secrets exclusively for simulator tests. Never attempt extraction or guessing of OEM secrets.

**Option 2: BCM.dll native provider.** First verify x86 `GenerateKeyEx` ABI from native OEM/Vector header or equally authoritative source: calling convention, full signature, string encoding/indirection, return enum success value, `iSecurityLevel` mapping, key buffer and actual-length. `AN-IDG-1-017` is background reference only until actual content/version is available. The separate `GenerateKeyExOpt` Cdecl annotation doesn't prove `GenerateKeyEx` uses Cdecl. Only then implement native call inside the x86 subprocess (never 64-bit GUI). Validate pinned DLL hash, block unexpected exports/dependencies, handle timeout/crash and zero sensitive owned buffers where feasible. Compare **every** authorized VF5NP/BCM L1 reference vector from ignored local `output/qa_commit81/reference-vectors.private.json` against real native outputs *byte-for-byte*; report only counts, lengths, hashes and pass/fail. The existing report identified 18 L1 and 18 L2 exchanges, but L2 is out of scope. If ABI or vector check fails/unknown: provider NOT READY.

Implement either option or both, but authorize real live submission only after verifiable provenance and offline match. Do not set `live_enabled=True` unconditionally, by environment variable or because of successful mock tests.

## Milestone C — Dedicated capability-bound generated-key request
1. Keep arbitrary manual `27 02 ...` disabled in the grid, import, and `DiagnosticRequest` constructor. Do not accept a user-entered key row as equivalent to a real generated key.
2. Create a non-forgeable-in-normal-GUI-flow, short-lived, one-time `SecurityKeySubmission`/capability issued only by `SecurityAccessSession` after `SEED_RECEIVED` and validated real provider result. Bind it to exact vehicle, ECU, TX/RX physical IDs, connection/capture generation, diagnostic-session epoch, test step/transaction id, odd subfunction `0x01`, seed expiration and provider fingerprint.
3. In the CAN owner command boundary, admit *only* capability-verified `27 02 + 16-byte key`, and only on authorized test bench with explicit per-send operator confirmation. No raw-key logging or persistence. Ensure state/memory invalidation on timeout, reconnect, ECU change, session control `10 xx`, document revision, cancellation, duplicate send, or stale calculation.
4. Route key TX through existing ISO-TP owner pipeline, not a parallel transport. Use the established pending `7F 27 78` logic and full transaction IDs/response matching. No automatic retry (particularly after `7F 27 35/36/37`), no automatic extra security levels. Underlying CAN driver TX-success does not mean unlock.
5. Respect thread affinity: DLL computation in worker, GUI updates through signals; never block PySide6 main thread.

## Milestone D — Response semantics and UX
- Valid **seed** success: exact `67 01` prefix + 16-byte seed (only if verified profile expects that length). Reject mismatched echo, zero-length, malformed or stale frames.
- Valid **key submission**: `27 02 + 16 bytes` generated for the current seed/session.
- Valid **unlock**: positive UDS payload **exactly** `67 02`, correlation to the outstanding key transaction and correct ECU RX. Only then state `UNLOCKED`, Result `Passed`, notice `Security Unlocked (Level 1)`.
- `7F 27 78`: response pending, not success or failure until concluded/time limit. `7F 27 35` invalid key; `36` attempts exceeded; `37` delay not expired; `33` security access denied. Timeout/malformed/unexpected positive/transport error => FAIL or Error, never unlocked.
- Display states `Seed received`, `Calculating key`, `Key calculated`, `Awaiting bench confirmation`, `Sending key`, `Security Unlocked`, `Failed/Cancelled/Expired`. Add a deliberate `Unlock L1` action rather than auto-sending as soon as seed arrives. Do not pop a new dialog on every unrelated SID or reset existing sequence results when ECU changes.
- UI never shows real raw seed/key in generic notices, exports, exception traces or telemetry. Existing manually requested response-view behavior may be retained with appropriate caution.

## Milestone E — Test matrix and release evidence
- Unit: HMAC with **dummy** public test vector; 16-byte lengths; false provider `mock_only=False`; provider provenance mismatch; exact `67 01` / `67 02`; `7F 27 33/35/36/37/78`; stale result; reused capability; double click; disconnected; cancelled; changed ECU/vehicle/ID/session; expired seed; missing DLL; x86 worker crash/timeout; no secrets in shared logs.
- Offline native: all 18 L1 BCM reference vectors matched byte-for-byte or mark BLOCKED. No live ECU calls during verification.
- Simulated ECU end-to-end: `10 03 -> 50 03`, `27 01 -> 67 01 + test seed`, mock **simulator-only** key generator, generated `27 02 + test key`, `67 02`. Also invalid-key NRC and timeout cases. Test using the **same** CAN owner path by a fake/mock transport; ensure mock-derived keys cannot be routed to a real adapter.
- Regression: CAN Monitor / Vector discovery / ISO-TP segmentation / BLF capture / Log Analyzer / vehicle resource configuration / license / sequence editing. Record test counts and *baseline* failures separately.
- Report: `docs/can_interface/COMMIT82_SECURITY_ACCESS_REPORT.md` with exact files, evidence, tested vs blocked, audit of all send policy gates, and recommendation for physical bench trial. Exclude proprietary DLL, secret key and raw reference vectors from Git.

## Acceptance and stop conditions
**Simulator PASS:** full `27 01 -> 67 01 -> calculate -> 27 02 -> 67 02` proven in tests.
**Real provider PASS:** exact DLL ABI or approved HMAC profile established, offline vector matches and resource fingerprint bound to vehicle/ECU.
**Physical send ready:** simulator PASS + real provider PASS + one-shot owner capability + explicit connected-bench permission/confirmation + regression checks. Only then enable the guarded `27 02` action. Otherwise ship simulated flow and clearly mark physical `27 02` BLOCKED. Never fabricate ECU success.

## Deliverable format
Implement code and tests (not merely plan), working in small increments. Provide modified-file list, how to run tests, offline-vector evidence, unverified assumptions, and release decision. Do not rewrite established app architecture, reimplement a second CAN transport, guess OEM secret/calling convention, add blanket security service allowances or claim live hardware passed without test results. Do not commit/push without user instruction.
