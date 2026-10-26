# Commit 64 - ECU drafts and CAN sequence sidebar editor

Baseline: commit 63, `37e0f1be3310b7981574b84554483a6cf8107948`.
Specification: `.codex/skills/can-sequence-editor-commit64/SKILL.md` (revised footer placement).
No commit or push was created. No native CAN, ISO-TP, SecurityAccess, Seed-Key execution,
BLF implementation or portable DLL storage transaction was changed.

## Sidebar layout and document architecture

All five actions are children of `CanSequenceSidebar.footer`, outside the scrolling
QListWidget, with exactly two compact rows:

```
+ Add       Import SEQ       Export SEQ
Save                        Save Order
```

The list alone has stretch factor 1 and a themed vertical scrollbar. There is no nested
scroll area or sidebar horizontal scrollbar. Error, selection and feedback labels have
bounded height. Invalid-source details remain available through the error tooltip;
malformed files are neither removed nor overwritten. Buttons reuse PrimaryButton and
SecondaryButton; dirty document Save is primary. Redundant header Save is hidden while
its compatibility signal remains usable. Header Add Row and Load .diag remain separate
row/file actions, not duplicates of the five footer document actions.

CanWorkspaceController owns add/import/export/Save, reuses its existing sequence repository
and view preference store, and remains separate from CAN transport. New sequences have
session-only UUID draft identities and no file until Save. Add validates a distinct name
and respects Save/Discard/Cancel for a dirty active document. Display names may duplicate:
file identity is the absolute source path, not label text. Pending order and document dirty
are independent; successful document Save clears only its title/item asterisk.

Save Order persists only file-backed identities. A moved unsaved draft retains its position
when Save gives it a file identity, then requires explicit Save Order. Clicking Save Order
before that draft is saved explains the prerequisite rather than persisting an unrestorable
UUID. An untouched new draft does not create a false order asterisk on Save. Native Save As
keeps the original file identity/order and adds the copy separately. Draft add/remove also
resynchronizes visible Select All, checked-ID signals and selected count. Synchronous list
refresh still snapshots item data before emitting, preserving the Commit 59 lifetime fix.

## ECU draft lifecycle

EcuDraftController snapshots eight exact text fields (name, request/response IDs, DLL, ODX,
DBC, DTC, request library) plus explicit DLL Browse intent. Its key is `(Vehicle, ECU)` using
the saved canonical name. Snapshot/selection changes never validate through mutating getters,
copy a DLL or write JSON. Saved ECU objects remain unchanged and remain CAN's source of truth.
Returning to EPS restores its draft and Browse intent, even after viewing another ECU/Vehicle.

ECUList stores canonical names in an item role and shows a separate ` *` suffix. Sorting,
selection and Save/Delete use canonical identities, not decorated text. A themed right-click
`Discard ECU draft` action snapshots both Vehicle and ECU before execution and discards only
that key. Save failure retains the draft; successful Save clears only its original key and
reloads the Commit 63 portable resource. Rename clears that saved key without disturbing
other drafts. Existing duplicate/case-only rename/storage guards remain in force. Confirmed
Delete explicitly discards the deleted ECU/Vehicle drafts; cancelled/failed Delete retains them.
Cleanup warnings after a committed storage operation reload the saved state and clear that draft.

Drafts are session-only, not an additional persistence database. App restart restores saved
configuration; unsaved drafts are not restored. Theme refresh does not validate or modify data.

## Table, ECU resolution and clipboard exchange

The visible editable Test sequence name column is between Step and ECU. Checkbox and manual
`>` columns remain. Column handlers, runtime rendering and theme mapping use updated constants.
Name/comment/delay/repeat edits keep manual results; ECU/request/expected/match edits retain
step-scoped invalidation. Existing step IDs survive normal edits and append import.

With a selected, available Vehicle, unknown, blank or ambiguous ECU selectors are empty and
non-sendable. Original imported model text is retained for reversible display and diagnostics;
changing to a matching Vehicle can resolve it. Without an available Vehicle, original text is
displayed rather than emptied, but send stays disabled. Clearing a valid selector explicitly
sets the model ECU to blank, so it cannot send to the previous hidden target. Backend send
policy and addressing validation remain unchanged and still protect direct service calls.

Before Save, unresolved targets are reported with row/original name. Explicit Save writes
blank ECU targets for these rows; the active-document diagnostics retain the originals and
remain available in the bounded notice/tooltip. This report is session-only. Merely opening
or switching Vehicle does not normalize the original file. No-vehicle Save preserves original
names. .diag sources remain read-only and require Save As native JSON.

The clipboard codec is pure and shares one nine-column definition for preview/export:

```
Step | Test sequence name | ECU | Payload(HEX) | Delay(ms) | Repeat | Expected Response (HEX) | Results | Comment
```

Import accepts TSV or correctly quoted CSV with an exact header, validates all rows before
application, reports source line numbers and supports quoted comment tabs/newlines. Limits:
2,097,152 text characters and 2,000 imported rows (the CSV parser also applies its field limit).
Payload/expected HEX, positive unique Step, nonempty sequence name, nonnegative optional delay,
and repeat >= 1 are validated. Preview must succeed and an explicit Append/Replace mode must
be selected. Input edits invalidate preview. Applied rows are renumbered in source order as
the preview explains. Replace starts fresh step IDs/runtime; append retains existing results
and adds new IDs. Imported Results are diagnostic information only, never Passed runtime.

Export opens a modal read-only preview with Cancel/Copy. Copy writes the complete deterministic
quoted TSV to the clipboard and never writes an arbitrary file. Unsaved editor values are used;
only actual existing runtime contributes Results, and unrun rows are blank. User text is shown
as plain text/escaped tooltips. There is no new TX, automatic sequence execution or live 0x27.

## Persistence and compatibility

CAN JSON retains schema_version 1 and the existing fields; runtime never enters JSON. The CAN
repository accepts blank ECU targets for incomplete/non-sendable editor rows and preserves
comment whitespace. The shared strict repository keeps its previous nonempty-ECU default:
fill targets before handing incomplete documents to strict legacy consumers. CAN saves use
fsynced same-directory temporary JSON plus atomic replace; failed Save retains dirty state
and the original file. No Vehicle JSON/DLL migration or change to DLL path-base semantics occurs.

## Verification and actual results

Actual commands, with local QA helpers under ignored `output/qa_commit64/`:

```powershell
.venv\Scripts\python.exe output/qa_commit64/run_validation.py commit64
.venv\Scripts\python.exe output/qa_commit64/run_validation.py can
.venv\Scripts\python.exe output/qa_commit64/run_validation.py m5b
.venv\Scripts\python.exe output/qa_commit64/run_validation.py vehicle
.venv\Scripts\python.exe output/qa_commit64/render_ui.py
.venv\Scripts\python.exe -B output/qa_commit64/ordered_probe.py
git diff --check -- gui core repositories tests tasks
```

The focused runner loads `tests.core.test_sequence_exchange`, `tests.gui.test_ecu_drafts`
and `tests.gui.test_can_sequence_editor64`. All use temporary synthetic data. The broader
runner reuses the M05B CAN/ISO-TP/BLF/manual policy, DLL/provider and Vehicle module sets,
isolates default preferences, and blocks static inspection of real external DLL references.

| Final suite | Tests | Passed | Failed | Errors / skipped |
|---|---:|---:|---:|---:|
| Commit 64 focused | 17 | 17 | 0 | 0 / 0 |
| CAN M01-M04B / commits 59-63 regression | 254 | 254 | 0 | 0 / 0 |
| M05A/M05B portable DLL/provider | 36 | 36 | 0 | 0 / 0 |
| Vehicle service/export/selector | 43 | 42 | 1 baseline | 0 / 0 |
| Distinct total | 350 | 349 | 1 baseline | 0 / 0 |

The baseline failure is `test_vehicle_manager_has_display_names_import_button`: expected
`Import Display Names`, baseline actual `Import File Display Names`. It was reproduced
against VehicleManagerTab compiled in memory from commit 63 (`git show HEAD`), without
changing that unrelated label.

An intermediate CAN run exposed the old connection-only FakeCANBackend missing
`fn_receive_frame`; continuous monitoring could fault with AttributeError and clear the
connection tooltip before assertion. The connection test fixture now returns no frame,
satisfying the existing RX contract. Its slow-connect/disconnect test and the full 254-test
suite pass afterward. Production Vector/backend/connection owner/monitor code is untouched.

Regression covers EPS Browse -> BCM -> EPS -> Save/reload, multiple Vehicle drafts, errors,
scoped discard, portable paths, theme, unknown/blank/no-vehicle targets, no stale-target send,
visible sequence-name edit, failed Save dirty retention, two-row footer with long list/error
overflow, checked state/lifetime, duplicate labels, explicit import mode/atomic failure,
quoted TSV/CSV, Results ignored on import, Cancel/Copy, .diag Save As, pending-order independence,
draft drag identity conversion, Save As original identity, Steps 1-4 runtime preservation,
and existing CAN connection, ISO-TP, manual authorization, continuous capture and BLF round-trip.

18 changed/new Python files compile successfully. Diff whitespace checks pass. Before/after
SHA-256 comparison confirms all 17 pre-existing user-edited Vehicle JSON files are byte-for-byte
unchanged. The user-supplied skill directory is also untouched.

## Visual checks and limits

Offscreen PySide widgets were inspected with Segoe UI in both themes. Long-list scroll and
12 invalid sources were present; the footer geometry stayed fixed before/after scrolling:

| Window | Sidebar width | Footer height |
|---|---:|---:|
| 1366 x 768 | 339 px | 66 px |
| 1600 x 900 | 398 px | 66 px |
| Default 1200 x 800 | 297 px | 66 px |

All five labels fit without clipping and there is no sidebar horizontal scrollbar. The wider
diagnostic table keeps its normal independent horizontal scrolling. Local images are
`output/qa_commit64/LIGHT-1366x768.png`, `DARK-1600x900.png`, `DARK-1200x800.png`, and
`EXPORT-LIGHT.png`/`EXPORT-DARK.png`; complete sets exist for both themes and all three sizes.
MainWindow declares an initial 1200x800 size, not an explicit smaller supported minimum.

Independent review identified stale ECU clearing and two draft/order/count lifecycle bugs;
each was reproduced with a failing test and corrected. One reviewer-only reordered Qt test
harness also reported native access violation 0xC0000005. Main could not reproduce it: the
ordered three-test probe passed, the five-test probe with the same audit guard and temporary
CWD inside the workspace passed 5/5, and the normal 17/254 suites pass. Its cause remains
unconfirmed; no global exception suppression or production Qt workaround was introduced.
Native GUI soak testing remains a limit.

No physical Vector hardware, OEM DLL execution, Excel application paste, or interactive native
dialog clicking was tested. Clipboard contents/round-trip and real offscreen Qt widgets were
tested. Import preview/table population are bounded but synchronous; very large inputs can
still pause the UI. Session diagnostics/drafts are not persisted across restart.

## Modified files

- `core/sequence_exchange.py`: canonical TSV/CSV schema, validation and serialization.
- `gui/dialogs/sequence_exchange_dialog.py`: themed preview/mode/apply and Cancel/Copy.
- `gui/controllers/can_workspace_controller.py`: footer actions and draft/file persistence lifecycle.
- `gui/widgets/can_interface/sequence_sidebar.py`: fixed footer, bounded errors, draft IDs/order/count.
- `gui/widgets/can_interface/diagnostic_table_panel.py`: column mapping, import/runtime and ECU resolution.
- `gui/widgets/can_interface/current_test_case_panel.py`: escaped plain-text tooltips.
- `gui/controllers/ecu_draft_controller.py`: session-only field snapshots and scoped lifecycle.
- `gui/tabs/vehicle_manager_tab.py`: selection/Save/Delete draft hooks.
- `gui/widgets/vehicle_manager/ecu_list.py`: canonical item IDs, dirty markers and scoped Discard menu.
- `gui/widgets/vehicle_manager/ecu_resource.py`: successful Browse notification after import intent is set.
- `repositories/can_sequence_repository.py`: atomic native saves, blank draft ECU/comment handling.
- `repositories/diagnostic_sequence_repository.py`: strict-by-default ECU validation extension point.
- `tests/core/test_sequence_exchange.py`: codec validation and quoted data.
- `tests/gui/test_ecu_drafts.py`: draft isolation, retained import intent and failure/discard/theme.
- `tests/gui/test_can_sequence_editor64.py`: editor/footer/import/export/order regressions.
- `tests/gui/test_can_diagnostic_table_panel.py`: restored column schema and explicit Vehicle setup.
- `tests/gui/test_can_step_runtime.py`: sequence-name edits preserve existing manual results.
- `tests/gui/test_can_connection_tab.py`: complete no-traffic RX fake contract.
- `tasks/plan.md`, `tasks/todo.md`: Commit 64 decisions and checkpoints.
- `docs/can_interface/COMMIT64_SEQUENCE_EDITOR_DRAFTS_REPORT.md`: this report.

Suggested commit: `can interface - commit 64: Preserve ECU Drafts and Enhance Sequence Sidebar Editor`.
