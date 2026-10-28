---
name: vcode-security-access-commit81
description: Implement and verify V-CODE SecurityAccess 0x27 Level 1 from Commit 80 with a separate x86 DLL worker and guarded 27 02 transmission.
---

# V-CODE CAN Interface — Commit 81 Security Access (27 01 → 27 02)

## Mission
Extend `dathp95/UDS-Analysis` after Commit 80 (`58ff2ed8c994ece126e00e9a010e16462d8bf74e`) to support an explicitly authorized, operator-confirmed SecurityAccess Level 1 exchange on an ECU test bench. Implement the entire lifecycle from `27 01` through key generation and `27 02`, but do not enable real ECU key submission unless the DLL ABI and offline reference vectors are independently validated. Keep all existing diagnostic behavior, logging, and sequence editing intact.

## Sources and established facts
- Existing project modules: `core/diagnostic_request.py`, `gui/controllers/can_diagnostic_controller.py`, `gui/widgets/can_interface/diagnostic_table_panel.py`, `services/can/security_seed_parser.py`, `services/can/security_key_service.py`, `services/seed_key_provider.py`, `services/vehicle_service.py`, `services/ecu_dll_resource.py`, `core/dll_resource.py`, `core/vehicle_dll_paths.py`, `core/bench_authorization.py`.
- Vehicle Manager stores the ECU DLL reference as `ecu.resources['dll']`, with path base in `ecu.resources.get('dll_path_base', 'project')`. Prefer `VehicleService.resolve_ecu_dll_resource(vehicle_name, ecu_name)` for immutable static metadata; do not add a duplicate resolver.
- BCM DLL is x86, exports `GenerateKeyEx`. The managed CBT `HandleDLL.cs` has a 7-parameter `GenerateKeyEx` delegate and an 8-parameter `GenerateKeyExOpt` delegate. Only the latter was visibly annotated Cdecl in the original uploaded source; calling convention and string marshalling for `GenerateKeyEx` are **not verified**. The body of `HandleDLL.CalulateKey()` was not recovered.
- CBT `SendDataMessage()` performs: request odd 0x27 subfunction, check positive response, discard two response header bytes, call `HandleDLL.CalulateKey(seed, request_subfunction, ref key)`, then send `27 [subfunction+1] + key`. This confirms orchestration but not the native ABI or level mapping.
- UDS Level 1 response matching: `27 01` -> `67 01 + seed`; `27 02 + key` -> `67 02`. Reject `67 02 + seed` as a valid response to `27 01` unless independently proven through raw CAN data.
- Reference workbook `EEIV_LogAnalyzer_Report_VF5NP_20261028_170829.xlsx` includes successful BCM L1/L2 exchanges; compare offline without logging sensitive bytes. Inspect real workbook rather than copying assumed values. DLL candidates may differ (e.g. 857600 vs 30720 bytes). Confirm exact DLL SHA-256 before testing.

## Required implementation phases

### Phase A — Audit current source and baseline tests
1. Read current files before changes. Note any commits after 80 and preserve their behavior.
2. Identify exact existing 27 01 and 27 02 validation gates in both GUI and core. Do not simply append `b'\x27\x02'` to the `SECURITY_SEED_REQUESTS` set, because 27 02 requires a variable-length generated key and separate validation.
3. Run baseline existing tests and record failures unrelated to this change.

### Phase B — Offline reference-vector analysis
1. Read the spreadsheet with `openpyxl`. Extract full UDS payloads only for request/response pairs attached to the same ECU and chronological session. Classify positive/negative responses and all matching 27 01 → 67 01 → 27 02 → 67 02 sequences.
2. Validate that seed/key lengths are consistent across reference exchanges; never hardcode 16 bytes solely because one BCM log shows that length.
3. Keep vectors in a local, gitignored test-fixture location. In shared reports output only counts, lengths and keyed pass/fail or hashes, never raw seeds or keys.

### Phase C — Native DLL boundary (no live sending yet)
1. Use the existing VehicleService resolver; distinguish missing DLL, unsupported architecture, export unavailable and unverified ABI.
2. Build an out-of-process **x86** worker interface with a typed request/response and bounded IPC. The Python 64-bit GUI must not load a 32-bit DLL in-process.
3. Worker supports cancellation, per-request timeout, killed/crashed-worker detection, key-length validation, exit cleanup and no plaintext key/seed logs. Do not persist secrets in temp files.
4. The worker may initially be mock-only. **Do not invoke native GenerateKeyEx until the exact ABI is validated against a header or trustworthy vendor specification**, including calling convention, char-pointer/string encoding and indirection, key output length, return enum, and mapping of UDS subfunction to `iSecurityLevel`.
5. Once ABI is verified, compare generated keys to authorized offline test vectors. Do not assert matching based on `VKEY_GEN_OK` alone. Abort on any mismatch.

### Phase D — SecurityAccess state machine and guarded send
1. Add explicit state transitions: IDLE → SEED_REQUESTED → SEED_RECEIVED → KEY_CALCULATED → KEY_SUBMITTED → UNLOCKED / FAILED / CANCELLED. Store session identity, selected Vehicle/ECU, TX/RX CAN IDs, 27 subfunction, transaction ID, connection generation and monotonic expiry.
2. Invalidate seed/key on ECU switch, Vehicle switch, reconnect/disconnect, DiagnosticSessionControl change, timeout, failed response, cancellation or stale generation.
3. Require an authorized connected bench and explicit user confirmation *for each live key submission*. Verify the same ECU and session before sending. No background unlock, retries or automatic escalation to other levels.
4. For Level 1 only, construct `b'\x27\x02' + key`, where `key` is returned by a validated **real** provider from the current session seed. Reject empty, stale, mock or failed results. Keep `27 02` disabled for arbitrary manual text rows unless the guarded workflow has prepared a validated key.
5. Use the established CAN/UDS transport and owner-thread diagnostic request pipeline for all transmissions; no parallel CAN bus thread or bypassing core validation. Create a narrowly scoped trusted request type/path to permit this one generated payload, while retaining all protections for other 27xx commands. Preserve normal confirmation and transaction matching.
6. Consider the ECU unlocked only upon an exact valid positive `67 02` response. Handle `7F 27 33/35/36/37/78`, timeouts, unexpected positive response and transport failure as non-success. Do not retry invalid keys automatically.
7. UI should distinguish `Seed received`, `Key calculated (offline)`, `Ready for authorized submission`, `Unlock successful`, `Unlock failed`. Do not display the raw key by default or leak it into notices, logs, Excel reports, debug dumps or exceptions.

### Phase E — Tests and release gate
- Unit tests: malformed positive/negative responses; wrong subfunction; stale generation, ECU, session, and connection; mock provider rejection; invalid key length; worker timeout/crash; DLL mismatch; false success messages; double-click/re-entrancy; concurrent operations; no logging of raw key.
- Offline tests: verify every authorized reference vector without sending to CAN.
- Integration tests: simulated CAN owner with `10 03`, `27 01`, validated 27 02, `67 02`, negative responses and cancellation.
- Live testing on bench only after explicit permission and ABI/vector verification; never use live ECU as an oracle to guess ABI or algorithms.
- Acceptance: no regression in existing CAN monitoring/BLF/UDS/log analyzer; tests green; safety gates demonstrably enforced. If blockers remain, ship UI and worker scaffold with live `27 02` still disabled, and report exact blockers.

## Work method and output
Implement smallest logically coherent increments with filenames, patch summaries, focused tests, and run commands. Do not claim any key can unlock a live ECU until independently confirmed. Do not modify vendor DLL or commit proprietary DLL, reference keys or seeds to Git. Output a concise review table of implemented, tested, and blocked items, with source references.
