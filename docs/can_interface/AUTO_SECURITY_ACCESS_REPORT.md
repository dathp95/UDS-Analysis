# One-action Auto SecurityAccess L1

Date: 2026-10-29 (Asia/Bangkok). Reviewed baseline: Commit 82,
`4aaa19be4bdf3071a36afead34775e6e7965654a`.
Contract: `.codex/skills/vcode-auto-security-access/SKILL.md`.

## Rollout status

- **Simulator AUTO 27 01 -> 67 02 = PASS.** One row-button click, no confirmation
  dialog after simulator bench/Extended setup, two distinct UDS transactions and
  one final logical result. The existing owner/ISO-TP path is used throughout.
- **Physical BCM AUTO 27 01 -> 67 02 = BLOCKED / NOT TESTED.** No OEM DLL
  execution, native vector comparison or physical key submission occurred.
  Real ABI/profile verification and approved target-scoped workflow authorization
  are both required before a physical Auto implementation can be enabled.

## Commit82 review and architecture

Commit82 already has expiring identity-bound seed state, an asynchronous key job,
verified provider provenance, generated one-use key capabilities, exact 67 02
correlation and protected key capture. It treats the sequence row as one physical
request, so Expected 67 02 previously failed against intermediate 67 01. Its
separate Unlock L1 action deliberately requires another confirmation.

The new pure `AutoSecurityAccessL1` coordinator keeps the original logical request
and creates a distinct seed subrequest with expected 67 01. The generated key
request still comes solely from existing SubmissionAuthority and expects exact
67 02. UDS response correlation is unchanged: 67 02 never matches a seed request.
The coordinator's physical trace contains only transaction IDs, phase, outcome,
elapsed time and NRC; it retains no raw DiagnosticResult, seed or key payload.

`AutoSecurityController` is the Qt adapter. It keeps the logical row busy across
seed completion, asynchronous calculation and key response, checks the concrete
job sender/workflow identity and resolves current Vehicle Manager IDs before key
dispatch. The final row only becomes Passed when both the normal key result and
`SecurityAccessSession.finish_submission` accept the exact current 67 02.

CANService reserves one simulator workflow across the handoff. It binds target,
connection, owner/session epoch, bench grant, provider object and verification
gate. Unrelated requests cannot enter the reserved owner. Context is checked at
preflight, calculation handoff, owner admission and I/O. Cleanup checks ownership
without requiring expired authorization to remain valid. No JSON/environment flag
can enable physical Auto. The actual backend must be exactly SimulatedCANBackend.

## Visible behavior and testing instructions

In a test harness using the existing SimulatedCANBackend:

1. Connect with an explicitly authorized simulator bench context.
2. Send a separate 10 03 row and receive 50 03 for the same configured ECU.
3. Configure a row Request `27 01`, Expected `67 02`, then press `>` once.
4. Row stays Running during the seed/calculation/key phases. Successful final
   response displays Receive `67 02`, Result Passed and runtime Comment
   `Security Unlocked (Level 1)`.

The runtime Comment is an overlay, not a model edit: Save/export of sequence
configuration preserves its original comment/request/expected fields. Auto-only
temporary seed responses never appear as a mismatched final response.

Seed-only rows (Expected 67 01 or blank), other UDS rows and manual Unlock retain
their existing semantics and confirmation policy. Run Selected is not enabled.
The standalone simulator remains a test backend, not a new live device selector.
On a physical Vector channel, an Auto row fails preflight before sending seed;
there is no force-enable switch or automatic diagnostic-session change.

Synthetic transcript (UDS payloads, not raw CAN frames):

```text
Precondition: 10 03 -> 50 03, same authorized simulator ECU
One visible row click
Seed transaction A: TX 27 01 -> RX 67 01 [seed redacted, 16 bytes]
Verified simulator provider: [key redacted, 16 bytes]
Key transaction B: TX 27 02 [key redacted] -> RX 67 02
A != B; final logical row Receive=67 02, Result=Passed
```

All-zero valid-profile seed is reported Not Evaluated / Already unlocked with
actual response header 67 01, no key transmission and no fabricated 67 02.
NRC 24/33/35/36/37 terminates without retry; NRC 78 remains pending until final
response or timeout. A total workflow deadline also bounds asynchronous handoff.

## Privacy and cleanup

Auto seed RX designation is recorded at transaction start independently of the
workflow reservation. Seed/orphan CF streams stay private after cancellation;
recognized non-seed FFs open their own public CF stream. Key TX and matching
late driver echoes retain Commit82's privacy filtering. The logical row, notices,
trace and runtime overlay contain no raw seed/key or provider exception details.
Manual seed-only response viewing retains its established behavior.

Independent review found two implementation defects, both reproduced RED and
fixed: authorization expiry blocked owner cleanup, and unseen seed CFs could
reach capture after cancel. The final bounded review found no further required
issue in the reviewed paths. Existing cross-model-review opt-out was respected.

## Changed source and tests

- `services/can/auto_security_access.py`: pure composite state/result/trace.
- `services/can/can_service.py`: simulator workflow reservation and owner checks.
- `gui/controllers/auto_security_controller.py`: Qt orchestration adapter.
- `gui/controllers/can_diagnostic_controller.py`: exact opt-in, invalidation and
  result routing; manual key callback now also checks the actual job sender.
- `gui/widgets/can_interface/diagnostic_table_panel.py`: runtime Comment/progress
  overlay and Auto tooltip; no sequence schema change.
- `gui/workers/can_diagnostic_session.py`: private Auto seed capture lifecycle.
- `tests/services/test_auto_security_access.py`,
  `tests/gui/test_auto_security_access.py`: coordinator/owner/GUI end-to-end cases.
- `tests/gui/test_security_access82.py`: the old wrong-Expected seed test now uses
  67 03, since exact Expected 67 02 intentionally opts into Auto.

No second CAN connection, RX consumer, udsoncan client, new dependency, native
loader, license change, live-provider flag, commit or push was introduced.

## Verification

Initial Commit82 focused baseline: **43 tests, all passed**.
New Auto service/GUI suite: **30 tests, all passed** at the final focused checkpoint.
Auto plus existing Commit82 service/GUI checkpoint: **47 tests, all passed**
before additional negative tests were added.

```powershell
.venv\Scripts\python.exe -m unittest tests.services.test_auto_security_access tests.gui.test_auto_security_access -q
.venv\Scripts\python.exe -m unittest tests.services.test_security_access82 tests.gui.test_security_access82 tests.services.test_security_access_session tests.gui.test_security_access_session -q
```

The isolated all-module runner under ignored `output/qa_auto_security/` includes
namespace-package test folders that standard unittest discovery may omit. It
patches default UI preferences to temporary files and restricts DLL inspection
to synthetic temporary fixtures. Baseline mode imports changed modules from
`git show HEAD` in memory without resetting or replacing workspace files.
The full all-module attempt was not completed: unchanged MainWindow construction
tests remained exceptionally slow on both HEAD and final code. Those QA processes
were stopped; no passing full-repository result is claimed. Instead, regression
mode runs the established CAN/ISO-TP/BLF/sequence/Vehicle/Log Analyzer groups plus
startup/license and compares identical scopes against HEAD. Its exact counts and
remaining failures are recorded after completion.

Final established regression comparison:

| Scope | Tests | Passed | Failures | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: | ---: |
| HEAD Commit82 baseline | 474 | 451 | 21 | 2 | 0 |
| Final code including Auto | 504 | 481 | 21 | 2 | 0 |

The failure/error ID sets are identical: **zero new problem IDs**, zero removed
baseline problem IDs. All 30 new Auto tests pass in both focused and regression
runs. The 23 baseline problems concern existing editor/import/sidebar/Vehicle and
license assertions/errors. They were not suppressed or relabeled as passing.
Detailed IDs and tracebacks are local under `output/qa_auto_security/` in
`baseline-regression-results.json`, `final-regression-results.json` and matching
details files. No passing result is claimed for the interrupted all-module runs.

Local reproduction of the established comparison:

```powershell
.venv\Scripts\python.exe output/qa_auto_security/run_suite.py --baseline --regression
.venv\Scripts\python.exe output/qa_auto_security/run_suite.py --regression
```

Syntax checks passed for all 9 changed/new Python files, and `git diff --check`
passed. The 496 JSON configuration files retained aggregate SHA-256
`7975c2c4ee9fddccfd12fd78b69683c2c81f4b01f8826093af8c9b976df5ebfe`
at the verification checkpoint. Light/Dark renders were inspected at 1200x800
and 1366x768; additional captures show Expected/Receive/Results/Comment together.
All render fixtures are synthetic and stored only under ignored QA output.

## Native-provider and publication blockers

Unchanged from Commit82: supplied x86 GenerateKeyEx binaries are statically
identified, but the genuine calling convention, argument/string indirection,
success enum, security-level/variant mapping and proprietary inputs remain
unverified. HandleDLL.cs has an invalid helper body; gen.txt establishes managed
flow only. No native output has been compared to the 18 authorized L1 BCM
reference pairs. No approved OEM HMAC secret/profile is registered.

Physical one-click authorization is also intentionally not inferred from a
generic bench flag or imported Expected=67 02. A reviewed target/operation-scoped
workflow grant design is required alongside the real-provider proof.

Commit82 already tracks 129 diagnostic-sequence JSONs and 4 PDFs in its diff.
Publication rights and public-repository exposure were not independently verified;
these existing assets were neither copied into this change nor published/deleted.
Only synthetic fixtures and metadata-only evidence are added. The three existing
user JSON edits are preserved and checked by aggregate fingerprint.
