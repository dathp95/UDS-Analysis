# SecurityAccess L1 — Vector integration progress

Date: 2026-10-29 (Asia/Bangkok).

## Result and release boundary

The application now has an explicit Unlock L1 action and a tested, asynchronous
seed/key exchange through the existing CAN owner and ISO-TP stack. The seed
response stays in its sequence row; generated-key progress/result is displayed
separately in Current Test Case. No automatic key submission or retry is added.

**Physical OEM DLL integration is not complete or enabled.** The supplied folder
contains 16 x86 DLLs exporting GenerateKeyEx and a BCM hex dump, but no native
header. No OEM DLL has been loaded/executed; no physical CAN request was sent.
Zero real offline reference vectors were compared in this task.

## Sources and scope

- Vector AN-IDG-1-017 v1.1, 2020-07-08, sections 1.1 and 1.2.1/1.2.2:
  https://cdn.vector.com/cms/content/know-how/_application-notes/AN-IDG-1-017_SecurityAccess.pdf
- AUTOSAR DCM R20-11, section 7.6.2.8, including SWS_Dcm_00323 (zero seed):
  https://www.autosar.org/fileadmin/standards/R20-11/CP/AUTOSAR_SWS_DiagnosticCommunicationManager.pdf
- Qt for Python QThread lifecycle and queued signal delivery:
  https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html

Vector specifies raw seed input, level, variant, output-buffer capacity and actual
key size; GenerateKeyExOpt additionally takes DLL-specific options. This does not
establish the calling convention, success enum, level mapping, variant or proprietary
extra input of these exact OEM binaries. Export names alone cannot prove that ABI.
The existing 16-byte HMAC profile is application/OEM-specific, not a universal
Vector or ISO algorithm. This report is not an ISO conformance certification.

## Implemented application flow

1. Operator sends `10 03`, then `27 01` with Expected `67 01` (prefix).
2. Correlated seed response is retained with vehicle/ECU/IDs, connection,
   document revision, diagnostic-session epoch and expiry.
3. Unlock L1 becomes available only for a compatible seed, verified provider,
   authorized bench and confirmed Extended session for the exact target.
4. Key calculation runs in a parentless retained QThread; GUI remains responsive.
   Closing/deleting the tab invalidates the session without destroying a running
   thread. Provider exceptions never reach generic UI notices.
5. After calculation, an individual confirmation is requested without showing the
   key. Configured IDs are resolved before and after the modal dialog.
6. Existing one-shot authority prepares `27 02 + key`; the existing owner validates
   authority, target, connection, session and bench again at admission and I/O.
7. Only exact correlated `67 02` completes the generated-key exchange. NRC 78
   remains pending; terminal NRC 24/33/35/36/37 is described without automatic retry.

Manual `27 02`, `27 03` and arbitrary 27xx grid payloads remain blocked. The
SECURITY_SEED_REQUESTS whitelist was not broadened. Session control and ECU reset
invalidate owner security authority. A session confirmed on one ECU cannot
authorize another ECU, even on the same physical IDs.

Zero seed is recognized as already unlocked only at the current profile's valid
16-byte length; malformed lengths never establish unlocked status. All simulated
states are labeled Simulator. Changes of ECU/Vehicle/document/configuration,
disconnect, session change, expiry or cancellation invalidate material.

Generated-key TX frames and matching buffered driver echoes are withheld from generic
CAN Monitor/CSV/BLF. A bounded history of salted in-memory frame fingerprints also
recognizes delayed echoes after the driver's 1-second correlation expires, without
retaining raw key bytes. The actual CAN transmission is unchanged; the UI explicitly
states the capture omission. Seed responses retain existing response-view behavior.

## Files changed in this task

- `gui/workers/security_key_job.py`: asynchronous calculation and retained lifetime.
- `gui/controllers/can_diagnostic_controller.py`: action, readiness, confirmation,
  cancellation, fresh target resolution and independent key result signal.
- `gui/widgets/can_interface/current_test_case_panel.py`, `gui/tabs/can_interface_tab.py`:
  Unlock L1 button and separate key-result label, existing themes/accessibility.
- `services/can/security_access_session.py`: zero-seed handling and target-bound
  terminal identity; simulator status preserved after material is cleared.
- `services/can/can_service.py`: bind confirmed session to vehicle/ECU/TX/RX.
- `services/can/diagnostic_client.py`: SecurityAccess NRC explanations.
- `core/security_submission.py`: readable manual-policy rejection text.
- `gui/workers/can_diagnostic_session.py`: keep key TX bytes out of generic capture.
- Focused service/GUI tests, specification and appended task checkpoints.

Existing user changes in CAN/ISO-TP/security foundation were retained. Vehicle
configuration, diagnostic sequence JSONs, license, OEM binaries, release flags
and dependencies were not edited. No commit/push was made.

## Verification evidence

- Initial focused baseline: 16 tests, 11 pass / 5 GUI errors (missing Unlock L1).
- TDD reproduced missing zero-seed handling, cross-ECU session inheritance, modal
  CAN-ID change, malformed zero seed, overwritten seed response, misleading readiness
  and key bytes reaching capture. Each was fixed and regression-guarded.
- Focused security/client suite: 67 tests passed before final capture/status work;
  subsequent targeted GUI/session/capture suites also passed.
- Broad isolated regression before final capture/status work: 452 tests,
  432 pass / 18 failures / 2 errors. Nineteen problem IDs match the recorded
  Commit81 baseline. The remaining Vehicle caption assertion was independently
  reproduced with `git show HEAD` source (`Import File Display Names` versus
  expected `Import Display Names`). No tests were skipped or removed.
- Final focused suite: **68 tests passed**, including delayed, uncorrelated key
  echoes. Ten capture/echo/continuous-capture tests also passed after this fix.
- Qt Light/Dark renders were inspected at 1200x800 and 1366x768; seed and key
  results remain separate and the new controls fit at both sizes.
- All 12 changed Python source/test files parse successfully; `git diff --check`
  passed. Across the regression checkpoint, all 496 config JSON files retained
  aggregate SHA-256 `b64e0a1a72a34b4d2006b8b5acfc4305719f60bfeec4c68c5bdfd2f71c82c69e`.
- Startup/license regression: 21 tests, 18 pass / 3 existing UI text assertions
  fail (Activated badge formatting, failed-activation label and Details arrow).
  License source/tests are unchanged; no licensing code was edited.
- Final broad isolated regression on final code: **453 tests, 433 pass,
  18 failures / 2 errors, 0 skipped**. The same recorded baseline problem IDs and
  independently reproduced HEAD Vehicle caption assertion remain. Detailed
  failure IDs are in `output/qa_vector_security/regression-results.json`.

Reproduce focused tests:

```powershell
.venv\Scripts\python.exe -m unittest tests.services.test_security_access82 tests.gui.test_security_access82 tests.services.test_security_access_session tests.gui.test_security_access_session tests.services.test_security_seed_request tests.gui.test_security_seed_request tests.services.test_security_key_service tests.services.test_diagnostic_client -q
```

Local detailed QA is under ignored `output/qa_vector_security/`; it contains only
synthetic material, isolated runner results and Light/Dark renders.

## Remaining native-provider work

Obtain the actual OEM header/SDK and verify calling convention, return enumeration,
level/variant mapping, encoding, output capacity/actual-length and any proprietary
input. Then implement the exact native adapter in the separate x86 worker, bind
the canonical DLL fingerprint and compare all authorized offline L1 references.
The existing evidence describes 18 L1 BCM exchanges; this task did not compare
native outputs to them. Physical submission remains blocked until that succeeds.

BCM DLL inspected statically: 857,600 bytes, x86, GenerateKeyEx,
SHA-256 `412b4e91bcf7aa7804cda0de6d83ea13a3425810c3507ba78f6dab031a2150da`.

The user additionally identified `HandleDLL.cs` and `gen.txt`, both read in full.
`gen.txt` confirms the managed application's odd-subfunction seed request,
16-byte key buffer, call to `CalulateKey(seed, odd_subfunction)`, and subsequent
even-subfunction key submission. It does not show how that managed helper maps
arguments to GenerateKeyEx. `HandleDLL.cs` has an invalid/missing CalulateKey body;
only GenerateKeyExOpt has the Cdecl attribute. GenerateKeyEx has no explicit
calling convention and uses `ref string`, whereas the Vector note declares
`const char*`. The enum values and variant are absent. These fragments cannot
establish a native ABI or justify assuming the two APIs share a convention.
The missing helper body/header and VKeyGenResult definition remain necessary.

Independent review found and prompted fixes for target-bound session, modal
TOCTOU, malformed zero seed and delayed echo privacy; it also checked tab-close
worker cleanup. Findings were reproduced with failing tests before their fixes.
External cross-model review was offered; the user chose the existing review.
No external CLI was invoked.
