# M05B checkpoints

## Commit 83 — Auto SecurityAccess

- [x] Audit Commit82, baseline and configuration fingerprints.
- [x] Pure composite coordinator and redacted trace tested.
- [x] Simulator workflow reservation and physical preflight/owner gate tested.
- [x] One row click dispatches two existing transactions; runtime overlay only.
- [x] End-to-end success/negatives/cancel/privacy, regression and render (30 Auto tests pass).
- [x] Report simulator PASS separately from physical BLOCKED; final504 vs baseline474, same23 existing problems.

## Vector SecurityAccess completion

- [x] Read Vector AN-IDG-1-017; inspect supplied DLL headers/exports without loading.
- [x] Record focused baseline (16 tests, 5 missing-GUI errors) and scoped contract.
- [x] Zero-seed handling and session/result tests (profile-length validation).
- [x] Async Unlock L1, exact response, cancellation and one-shot GUI flow.
- [x] Focused/regression tests, render and independent review; pre-existing failures reported separately.
- [ ] Native provider: verify OEM ABI/parameters and all authorized offline vectors.

## Commit 82 checkpoints

- [ ] A baseline audit and source/asset hashes.
- [ ] B HMAC/provenance/offline verifier; report real-provider blockers explicitly.
- [ ] C one-shot generated-key capability at core/owner/TX boundaries.
- [ ] D deliberate async Unlock L1 and exact response state machine.
- [ ] E full simulator flow, negatives/cancellation/replay, regressions and report.

## Commit 81 checkpoints

- [x] A: audit baseline and independent manual 27xx gates; CAN baseline 9 failures/2 errors recorded.
- [x] B: 18 L1 + 18 L2 chronological reference exchanges, 6 parser tests, private ignored fixture.
- [x] C foundation: canonical DLL SHA-256/eligibility, actual x86 mock build, 9 IPC/process-tree tests.
- [x] D foundation: expiring seed lifecycle, cancellation/selection/connection UI integration; live gate closed.
- [x] E foundation: 30 new tests; broader regression/baseline comparison, review fixes, hashes and report.
- [ ] C release gate: trustworthy GenerateKeyEx ABI, real worker adapter and all offline key comparisons.
- [ ] D/E release gate: capability-bound live submission, exact 67 02 integration and authorized bench acceptance.

Evidence: docs/can_interface/COMMIT81_SECURITY_ACCESS_REPORT.md. Broad regression:
382 run, 363 pass, 17 failures + 2 errors identical to existing baseline problem
sets. No real DLL invocation or CAN key submission. Live gates remain blockers.

## Commit 64 checkpoints

- [x] Bounded TSV/CSV codec, quoted cells and validation atomicity.
- [x] Fixed sidebar footer, document actions, independent order and dirty indicators.
- [x] Sequence-name column, reversible unresolved ECU mapping and guarded send.
- [x] Per-Vehicle/ECU drafts including DLL Browse intent, scoped discard/save/delete.
- [x] Focused tests and Light/Dark layout checks at 1366/1600/default1200 widths.
- [x] Final regression, compilation, user-JSON hash comparison and implementation report.

- [x] Path contract + portable import, isolation/relocation and failure tests.
- [x] Browse/Save intent + persisted metadata + rename/delete lifecycle tests.
- [x] Typed mock-only provider/IPC and error/redaction tests.
- [x] Relevant CAN/UDS/ISO-TP/BLF/Vehicle regression and Light/Dark checks.
- [x] Final diff review, compile checks and M05B report with actual counts.
