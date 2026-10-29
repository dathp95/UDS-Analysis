# M05B implementation plan (commit 62 baseline)

## Commit 83 — one-action Auto SecurityAccess

Contract: `.codex/skills/vcode-auto-security-access/SKILL.md`; baseline HEAD
`4aaa19be4bdf3071a36afead34775e6e7965654a`. Preserve the three pre-existing JSON edits.
1. Audit/baseline existing Commit82 gates, worker handoff and public asset names.
2. TDD a pure coordinator: distinct seed/key transactions, redacted metadata trace,
   exact final 67 02, zero-seed Not Evaluated, duplicate/negative/timeout handling.
3. Add service-owned simulator-only workflow reservation with target/bench/epoch/
   provider checks at preflight and owner boundaries. Physical Auto remains blocked
   pending real ABI/vectors and approved target-scoped workflow authorization.
4. Integrate a thin Qt adapter and runtime-only row comment/progress overlay.
   Reuse SecurityKeyJob and CAN owner; no second dialog in pre-authorized simulator.
5. Execute end-to-end simulator negatives/cancellation/reentrancy/privacy tests,
   existing manual suites, broad regression, Light/Dark render and final review.

Verify: `.venv\Scripts\python.exe -m unittest tests.services.test_auto_security_access tests.gui.test_auto_security_access -q`.
Report: `docs/can_interface/AUTO_SECURITY_ACCESS_REPORT.md`; no commit/push or asset copy.

## Vector SecurityAccess completion (2026-10-29)

Contract: `docs/can_interface/VECTOR_SECURITY_ACCESS_SPEC.md`.
Preserve existing Commit82 changes and configuration. Baseline: 16 focused
tests, 5 GUI errors (missing Unlock L1). Implement zero-seed semantics and
asynchronous deliberate Unlock L1 through existing verified provider/owner.
Validate cancellation, selection changes, exact 67 02, NRC/pending, no retries,
and unchanged manual 27xx gates. Render Qt Light/Dark and run regressions.
Supplied native DLLs inspected statically only; physical provider remains
unavailable until OEM ABI/parameters and offline reference vectors are proven.

## Commit 82 plan (baseline 52aebbb5)

Specification: `.codex/skills/vcode-security-access-commit82/SKILL.md`.
1. Audit owner/core/grid gates; baseline failures remain separate. Preserve user
   UI config and supplied PDFs. Read security PDF sections 3.3/3.8/3.9, not secrets.
2. Standard HMAC-SHA1-128 provider and offline comparison with typed provenance.
   Only registered approved profiles may issue real authority; none are supplied.
   Dummy simulator proofs are bound to a memory-only backend, never Vector.
3. A dedicated generated-key request with an opaque one-use owner capability,
   exact target/connection/session/seed expiry/provider binding. Validate at
   construction, owner admission and every TX; preserve raw manual 27xx blocking.
4. Memory-only simulated ECU and full existing QThread owner/ISO-TP path tests:
   manual 10 03, manual 27 01, deliberate Unlock L1, generated key, exact 67 02.
   Add async key job and statuses, cancellation, NRC/pending/timeout tests.
5. Regression, review, compile/hash/secret checks and Commit82 report. Native
   BCM ABI remains unverified; no real profile secret/vector approval exists.
   No live key submission, OEM DLL invocation, license changes or commit/push.

Verification: `.venv\Scripts\python.exe -m unittest
tests.services.test_security_access82 tests.gui.test_security_access82 -v`,
existing 81/seed/provider/owner/BLF/Log Analyzer groups via isolated QA runner.
Implementation follows existing frozen requests, pure services and Qt signals.
Trust boundaries: config/PDF/vector/provider/GUI intent are not authorization.
Simulator status must identify simulation; mock material cannot cross real owner.

## Commit 81 plan (baseline 58ff2ed8)

Specification: `.codex/skills/vcode-security-access-commit81/SKILL.md` (the requested
`.agents` path is absent). Existing milestones A-E are the acceptance contract.
No commit/push, vendor execution with guessed ABI, or live CAN testing is authorized.

1. A/B: audit current gates and baseline tests; extract chronological same-ECU
   reference exchanges with openpyxl into ignored local fixtures. Report only
   counts/lengths/hashes. Preserve user JSON and HandleDLL.cs hashes.
2. C: reuse VehicleService DLL metadata, pin SHA-256, report distinct eligibility
   blockers. Build an x86 .NET mock-only worker and bounded pipe adapter; test
   cancellation, timeout, crash, malformed IPC, process reaping and redaction.
3. D: add in-memory expiring SecurityAccess session identity/state and integrate
   seed lifecycle/status with manual diagnostics. Invalidate on context/session/
   connection changes. Keep core and GUI manual 27 02 denied while ABI/reference
   validation is unavailable. Never promote mock keys to live authorization.
4. E: focused unittest suites after each slice, CAN/UDS/BLF and Log Analyzer
   regressions, independent security review, compile/diff/config preservation
   checks and `docs/can_interface/COMMIT81_SECURITY_ACCESS_REPORT.md`.

Trust boundaries: workbook/config/IPC/DLL metadata are untrusted; no native
GenerateKeyEx call until trustworthy ABI evidence and all offline vectors pass.
Worker uses no CAN and no secret temp files. Real provider and live submission
remain release blockers rather than guessed implementations.

Commands: `.venv\Scripts\python.exe -m unittest tests.services.test_security_reference
tests.services.test_seed_key_worker tests.services.test_security_access_session
tests.gui.test_security_access_session -v`; build with
`powershell -File tools/security_worker/build.ps1`; use isolated local QA runner
for baseline/final wider suites. Source follows existing dataclasses/Enums and
unittest fixtures; no new dependencies or configuration schemas.

## Commit 64 implementation (baseline 37e0f1b)

Authoritative specification: `.codex/skills/can-sequence-editor-commit64/SKILL.md`.
1. Pure bounded TSV/quoted CSV codec and validation tests; results are informational only.
2. Fixed two-row sidebar footer and native draft document/controller/dialog actions;
   restore sequence-name column, retain stable step IDs and unresolved ECU diagnostics.
3. In-memory per-Vehicle/ECU field snapshots, including explicit DLL import intent;
   dirty indicators and scoped discard/save/delete/rename lifecycle.
4. Focused tests, CAN/UDS/BLF/portable DLL regressions, Light/Dark visual checks, report.
No CAN transport/security execution changes or commits. Protect pre-existing Vehicle JSON
edits with before/after hashes. Tests use temporary configs and synthetic PE fixtures.

The user-approved M05B skill is the specification and acceptance contract. Implement
portable per-Vehicle/per-ECU import on explicit Browse/update + Save; no OEM execution.

1. Path and storage slice: new imports use `resources/dll/<ECU>/<file>` plus the
   `resources.dll_path_base=vehicle` marker. Unmarked relative paths retain project-root
   semantics even if their prefix matches the new namespace. Retain absolute legacy references. Test isolation,
   relocation, invalid paths, checksums, version conflicts and rollback first.
2. GUI slice: explicit import intent through existing Controller -> Service -> Repository;
   Browse does not copy. Reload saved portable references and resolve static metadata.
   Test Save/Cancel/restart and resource-only refresh preserving completed diagnostics.
3. Mock provider slice: typed bounded IPC/correlation/errors, deterministic fake only,
   no loader or transport integration. Test timeout/cancellation/crash/redaction.
4. Review and verification: M04/M04B/60-62 regression, static PE fixtures only, Light/Dark
   render, compile/diff checks, report exact results and remaining recovery limits.

Storage decisions: version conflicting filenames, atomic same-directory publication,
streamed SHA-256 + copied PE revalidation, transactional JSON snapshots/rollback. Rename
imports the managed reference into the new ECU directory; deletion collects only formerly
referenced managed files after configuration commit and checks remaining references.
Do not touch native CAN ownership, authorization, monitor, BLF or 0x27 policy.

Commands: `.venv\Scripts\python.exe -m unittest tests.services.test_vehicle_dll_storage -v`
and focused GUI/provider suites, followed by the existing regression suites. Python
unittest and synthetic PE fixtures follow existing repository style. No dependency/schema
changes, OEM binary commits, automatic commit/push, or access to licensing/key material.
