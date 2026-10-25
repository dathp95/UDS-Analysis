---
name: can-m03-ui-layout
description: Implement V-CODE CAN Interface Milestone 03 UI only, matching the approved diagnostic workspace screenshot while reusing M01/M02, Vehicle Manager, existing sequence models, theme, controls, scrollbars and Save Order behavior.
---

# V-CODE — CAN Interface Milestone 03: Diagnostic Workspace UI ONLY

## 0. Mission, baseline and boundaries

You are a senior Python 3.12 / PySide6 engineer working on `dathp95/UDS-Analysis` (V-CODE). The current reviewed baseline is commit 55: `f5226fb5218d01510f454ef2dd7c8cc00015e0a7`. Before editing, verify the current HEAD and inspect newer changes if any.

**Goal:** Build the CAN Interface UI using the user's approved 1648×920-style desktop screenshot as visual guidance, but **inherit V-CODE's actual Light/Dark theme and existing components**, not the screenshot's hard-coded colors.

**This is UI-only M03.** Do NOT implement CAN TX/RX, ISO-TP, UDS requests, Seed-Key calls, real BLF recording, CSV export, diagnostic sequence execution, or background frame consumers. Provide UI interfaces and clear safe placeholders to connect in later milestones. Preserve every existing M01/M02 discovery/connection behavior.

**Hard rule:** Vehicle Manager / `VehicleService` is the one and only authority for ECU identity and its `request_id`, `response_id` and `resources['dll']`. Do not display/edit those fields in the CAN Interface table or an ECU-configuration panel, and do not create a second ECU database.

Do not silently overwrite existing `.diag`, vehicle files, licensing/configuration data, Log Analyze or Coding Value UI. Do not commit/push unless the user separately requests it.

## 1. Source inspection (MANDATORY BEFORE CODING)

Read latest versions of:

- `gui/tabs/can_interface_tab.py` (existing connected Vector UI and M02 worker wiring)
- `gui/workers/can_connection_worker.py`, `gui/workers/can_discovery_worker.py`
- `services/can/can_service.py`, `services/can/can_connection.py`, `services/can/vector_backend.py`, `services/can/owned_vector_bus.py`
- `gui/tabs/vehicle_manager_tab.py`; `gui/controllers/vehicle_controller.py`; `services/vehicle_service.py`; `repositories/vehicle_repository.py`
- `models/vehicle.py`; `models/ecu.py`; `gui/widgets/vehicle_manager/vehicle_selector.py`
- `gui/widgets/diagnostic/diagnostic_sequence_list.py`; `gui/widgets/diagnostic/diagnostic_sequence_table.py`
- `core/diagnostic_sequence.py`; `repositories/diagnostic_sequence_repository.py`
- `gui/widgets/coding_value/ecu_workspace_sidebar.py`; `gui/tabs/coding_value_tab.py`; `core/coding_value_workspace_store.py`
- `gui/tabs/log_analyzer_tab.py` and its sidebar/table widgets to learn existing layout conventions
- `gui/widgets/controls/primary_table.py`, `primary_button.py`, `secondary_button.py`, `action_button.py`, `primary_combobox.py`, `primary_lineedit.py`, `primary_checkbox.py`, `primary_label.py`
- `gui/themes/theme_manager.py`, `gui/themes/colors.py`, `gui/themes/styles/controls/table_style.py`, `gui/themes/styles/controls/scrollbar_style.py`
- `config/paths.py`, current `tests/gui/` and existing GUI theme refresh conventions

Reference screenshot: the user-provided CAN Interface screenshot in this conversation. If the screenshot is not available in Codex's local working directory, use the precise layout specification below; do not pretend to have read missing reference files.

Reference `.diag` sample files, if available to Codex: `0001.READ&CDS(1).diag`, `0002.READ VIN(1).diag`, `204.BCM&CDS&1.diag`, `9302.MHU&WriteVIN&1.diag`. They are JSON documents containing `Header` and `TestCaseItem`. Do not assume they are stored in GitHub. If absent, add small checked-in synthetic test fixtures matching the verified field names; do not invent real vehicle configurations.

## 2. Confirmed existing contracts; preserve them

**Vehicle Manager:** `VehicleService.list_vehicles()` and `.load_vehicle(vehicle_name)` load a `Vehicle` with `.ecus: list[ECU]`. `ECU` has `.name`, `.request_id` (str), `.response_id` (str), `.aliases`, `.resources` including `"dll"`. The current data is stored via `VehicleRepository`; do not read raw vehicle JSON directly from the UI.

**Diagnostic model:** `DiagnosticStep(step, sequence_name, ecu, request, delay_ms, repeat, expected_response, match, comment)` and `DiagnosticTestCase` already exist. `DiagnosticSequenceRepository` currently handles native `.json` sequences; it does **not** natively import external `.diag` schema. Existing `DiagnosticSequenceTable` has editing/validation/step renumbering, but not the approved per-row `>` button / visible Comment column. Preserve this older widget's behavior and tests, and introduce an adapter or a focused replacement/view on the same model; do not duplicate divergent business rules.

**Sequence list:** `DiagnosticSequenceList` already has list checkboxes, `sequence_selected`, `selection_changed`, numeric-prefix ordering, and scrollbar/theme support, but lacks the screenshot-style Search and explicit saved manual order. Extend carefully or create a dedicated `CanSequenceSidebar` wrapping shared behavior.

**Coding Value Save Order:** `EcuWorkspaceSidebar` has drag reordering, dirty indication, and an explicit `Save Order` action (`order_save_requested`). Unsaved reordering must not be inadvertently committed by an unrelated metadata save. Reuse the *behavioral pattern*, not the Coding Value workspace storage.

**M02 lifecycle:** CAN status must come from `CANService.snapshot` and existing `CANConnectionTask`/`CANDiscoveryTask`. Preserve connection worker lifetime, signal connections, cleanup/recovery behavior. Do not access a raw `VectorBus` in UI.

## 3. Target desktop composition — match screenshot first

Use a `QHBoxLayout`/horizontal `QSplitter` containing:

```
CANInterfaceTab  [orchestration ONLY]
└─ main_horizontal_splitter
   ├─ A. CanSequenceSidebar                    ~19–22% width
   └─ right_workspace                        ~78–81% width
      └─ right_vertical_splitter
         ├─ B. CanDiagnosticTablePanel          ~63–68% available height
         │  ├─ top toolbar: selected sequence title; Add Row / Delete / Load .diag / Save / Run Selected
         │  └─ table: [check] Step | ECU | Payload (HEX) | > | Delay (ms) | Repeat
         │           | Expected Response (HEX) | Receive Message (HEX) | Results | Comment
         └─ bottom_horizontal_splitter       ~32–37% available height
            ├─ C. CanSessionPanel              ~43–47% width
            │  ├─ existing Connection controls
            │  └─ read-only Current Test Case details
            └─ D. CanMonitorPanel              ~53–57% width
               ├─ toolbar: Monitoring status / Clear / Export CSV / Start BLF Log / Settings
               ├─ CAN ID filter + direction filter
               ├─ frames table: Time (s) | Dir | CAN ID | DLC | Data (HEX)
               └─ counters: Frames / Displayed / Dropped
└─ E. optional compact in-tab status strip: Vector / connection / device / channel / BLF
```

Make splitter ratios initial defaults, not hard-fixed dimensions. Use reasonable minimum panel dimensions and horizontal scroll for the wide diagnostic table. Test 1600×900 and 1366×768; avoid huge fixed minimum window sizes. Let table take priority when resized; do not cause the Diagnostic Sequence table to disappear.

**Do not add:** a standalone 'UDS Request' edit panel, ECU configuration editor, Request ID/Response ID/DLL columns, a second CAN connection bar, duplicate vehicle-management module, or extra top-level app tabs.

If active vehicle selection cannot be inferred reliably from existing app state, embed a **small existing `VehicleSelectorWidget`** in the table's toolbar or beside its title, while showing the actual chosen Vehicle name. This is a *vehicle selector* only, not an ECU editor. Never guess the vehicle from a `.diag` numeric `Header.IDVehicle` unless a verified mapping exists.

## 4. Suggested maintainable source structure

Create a dedicated feature package (names can adapt to existing naming conventions):

```
gui/widgets/can_interface/
    __init__.py
    sequence_sidebar.py              # Widget A: sequence selection/search/order
    diagnostic_table_panel.py         # Widget B: table + actions; row binding
    diagnostic_row_button.py          # Small themed > button / row action
    session_panel.py                 # Widget C composition, two sections
    connection_panel.py              # Extract/preserve M02 connection controls and glue
    current_test_case_panel.py        # Read-only selected-row details
    can_monitor_panel.py             # Widget D, display only in M03
    can_status_strip.py              # Optional; only if needed

# Non-GUI contracts, only when needed for UI correctness:
core/diagnostic_sequence_import.py    # .diag -> existing test-case model mapping
core/can_interface_ui_state.py         # view-state, selection, row display results
repositories/can_interface_ui_store.py # saved sidebar order/UI preferences (not ECU data)

tests/gui/test_can_interface_layout.py
tests/gui/test_can_sequence_sidebar.py
tests/gui/test_can_diagnostic_table_panel.py
tests/gui/test_can_session_panel.py
tests/gui/test_can_monitor_panel.py
 tests/core/test_diagnostic_sequence_import.py
```

Do not create empty modules merely to match this example. Consolidate trivial widgets sensibly, but never put all functionality back into `can_interface_tab.py`.

Ownership split:

- `CANInterfaceTab`: composition, high-level signals, selected vehicle/sequence, worker integration; **not** row painting, file parser or transport.
- Sidebar: search, sequence check selection, user order, saved-order state.
- Diagnostic table: per-row widget, editing, header sizing, row selection, emit typed action intent; no hardware calls.
- Connection panel: presentation of existing M02 controls and snapshot; no second CANService.
- Current panel: read-only selected step presentation.
- Monitor: display/filter/buffer placeholder APIs; no VectorBus reference.
- Core adapter: pure `.diag`/native step conversion; no Qt imports.
- UI store: safe persistence of display-only state; no .diag rewriting.

## 5. Task M03-UI-01 — Tab shell/layout

1. Refactor `gui/tabs/can_interface_tab.py` into a small orchestrator using the splitters above.
2. Preserve existing CANService instance and both worker tasks exactly once; do not instantiate an additional CANService in child widgets.
3. Extract existing Refresh/Connect/Disconnect controls and event handlers to a view/controller boundary without breaking M02 state machine, `RECOVERY_REQUIRED`, error displays or application quit.
4. Maintain `fn_refresh_theme()` orchestration; propagate to every new child.
5. Use `QSplitter.setStretchFactor()` and sensible default `setSizes()`. Persist splitter sizes only if an existing settings pattern makes it safe; otherwise postpone and document.
6. Preserve existing navigation and MainWindow behavior.

Acceptance: connection discovery, Connect/Disconnect/reconnect, theme, and existing diagnostic widgets still work. Screenshot-like proportions on normal laptop/desktop displays.

## 6. Task M03-UI-02 — Left Test Sequence sidebar

Layout: `Test Sequence` heading → `Search...` field → checkbox/list with scrolling → compact selected counter and `Save Order` (or context/toolbar action consistent with screenshot density).

- Reuse `PrimaryLineEdit`, `PrimaryCheckBox`, existing list patterns, styled scrollbar.
- Clicking a **sequence's name** previews/loads that sequence into the center table; checkbox indicates inclusion in the set selected for later batch execution. These are independent concepts.
- Provide `Select All` / clear selection honoring current filtering semantics; document whether selection applies to visible or all files. Do not surprise users by silently dropping hidden selections.
- Case-insensitive substring Search without mutating physical list or saved ordering.
- Support `.json` native sequences and imported `.diag` files; show which source failed to import with a concise error rather than breaking the entire list.
- Preserve numeric filename ordering on first load (e.g. `0001...`, `0002...`, `204...`, `9302...`).
- Manual drag reorder only when search filter is cleared, if introducing reorder; persist explicit `Save Order` using stable source identifiers. Mark unsaved order until saving; a separate comment edit/save must not commit the pending sidebar reorder.
- Reloading/new files: restore saved known order; append new sequences deterministically; keep selection when possible.
- No implicit run on check or click.

Signals: `sequence_open_requested(document_id)`, `checked_sequences_changed(ids)`, `order_save_requested(ids)` or equivalents.

## 7. Task M03-UI-03 — Diagnostic Sequence table

Exact visible columns and relative widths:

```
[✓] | Step | ECU | Payload (HEX) | > | Delay (ms) | Repeat |
Expected Response (HEX) | Receive Message (HEX) | Results | Comment
```

Recommended visual details:

- Row height about 32–36 px, modest borders, muted alternating row backgrounds from `PrimaryTable`.
- `Step` compact and center-aligned; `ECU` small combo from Vehicle Manager's **active vehicle**; `Payload` monospace; `>` ~30–36 px square-ish button via existing themed button styles, not inline HTML/text pretending to be a button.
- Delay/Repeat compact; Expected and Receive HEX wider, with text elision + full tooltip/copy access; Comment editable with tooltip.
- Non-editable runtime columns: Receive Message and Results.
- Prefer `PrimaryTable`; sort disabled by default to maintain execution Step order and row-to-model correctness.
- Header supports horizontal scroll, resizable column widths, no overlap. Make Results/Comment visible as far as possible; otherwise horizontally scroll.
- Selected row blue/highlight comes from `ThemeManager.fn_colors()` and shared `PrimaryTable` style, not screenshot RGB constants.
- Checkbox in each row selects rows for later **Run Selected**. A click on `>` targets exactly one row regardless of checkbox state.
- Row button emits a stable row/step identifier (not a captured stale table index). Re-resolve ID after add/remove/reorder to avoid wrong row execution.
- No click-to-execute from selecting the row or editing Payload.
- `Comment` persists using existing `DiagnosticStep.comment`; imported `.diag` `Remark` can initialize it.
- Edited `request`/`expected_response` must retain existing HEX validation; Delay integer/nonnegative; Repeat integer >=1. On validation failure revert or show in-place error, do not silently corrupt model.
- Add Row / Delete: reuse `DiagnosticSequenceTable`'s inherited-values and reindexing behavior. Confirm before destructive operations when appropriate.
- Save: reuse native `DiagnosticSequenceRepository` for `.json`. Imported `.diag` must **not** be overwritten or rewritten as `.diag`; offer safe 'Save As V-CODE Sequence (.json)' with existing model and preserve original file. No silent data loss for unsupported source fields.
- Save preserves row order, comments, selected vehicle association where supported by existing format; do not embed duplicate ECU request/response/DLL in sequence model.
- Runtime outcome API for future integration:
  `set_step_running(step_id)`, `set_step_result(step_id, received_payload, outcome, detail='')`, `reset_runtime_results()`.
  Keep runtime `Receive Message`, `Results`, performance details separate from persisted definition unless explicit report-save support already exists. No fake responses or fake Passed on load.
- Use neutral `—` initially. Future result states: Pending / Running / Passed / Failed / Timeout / Error / Not Evaluated. Use semantic theme colors. Matching policy is future UDS layer; no fake comparison without real RX.
- `>` button: render with proper style and tooltip. During UI-only M03, clicking emits an intent which controller handles as “Diagnostic execution not available until transport milestone”; NEVER send frames or simulate RX. Alternatively disable execution buttons with explicit tooltip until implementation. Be transparent to user.
- Batch `Run Selected`, `Stop` (if added): UI shell only; disabled/clearly not implemented until runner exists. Do not pretend batch execution works.

## 8. Task M03-UI-04 — Vehicle/ECU mapping

- Use `VehicleService` (or existing injected service) to load active Vehicle, and use `.ecus` for row ECU combos and validation.
- If active Vehicle is missing, clearly display `Select Vehicle`; do not silently pick a random vehicle.
- Resolve per-row ECU from the active Vehicle by exact `.name` and existing aliases only if their matching semantics are already verified. Missing or ambiguous ECU gets a visible warning marker/tooltip. Never silently substitute IDs from `.diag` `ECUObj`.
- `ECU.request_id` and `.response_id` remain strings used by future request builder. `ECU.resources['dll']` is managed in Vehicle Manager and **not displayed in CAN Interface**.
- When Vehicle changes, reload/rebind ECU options, preserve valid names, warn on incompatible steps, and never erase the original step or alter vehicle data automatically.
- If Vehicle Manager emits a `vehicle_data_changed` event through the hosting application, refresh the cached Vehicle responsibly; otherwise expose a refresh method without polling/disconnected duplicate data stores.
- Existing `VehicleSelectorWidget` is allowed in a small header location ONLY when required to select an active Vehicle. Do not place a large ECU configuration panel at the bottom.
- Keep a clear separation between imported `.diag` data and the canonical Vehicle Manager ECU config. Do not infer `Header.IDVehicle` -> Vehicle name without a verified mapping.

## 9. Task M03-UI-05 — Bottom LEFT session panel

Use one child container with **two visible subsections**:

### A. Connection (functional, inherited)
- Vendor: Vector (existing)
- Device: discovered device (existing)
- Channel: discovered channel (existing)
- Baudrate: existing selection
- Refresh / Connect / Disconnect / current state indicator/tooltip
- No extra link to Vehicle Manager inside this subsection.
- Preserve worker lifetime and all M02 error/RECOVERY_REQUIRED controls.

### B. Current Test Case (read-only)
When table row is selected, show Step `i / N`, ECU, Payload, Expected Response, Delay, Repeat, and optionally result status. Keep labels compact in two/few columns. If nothing selected show an empty state. This panel **never** has a Send button and should not edit the step.

## 10. Task M03-UI-06 — Bottom RIGHT CAN Monitor (visual shell)

Toolbar: `CAN Monitor`, optional Monitoring indicator (only green if real monitoring implemented in future), `Clear`, `Export CSV`, `Start BLF Log` / `Stop BLF Log`, settings if there is a real applicable settings panel.

Filter row: CAN ID filter input (HEX) and direction `All / TX / RX` dropdown.

Table columns: `Time (s) | Dir | CAN ID | DLC | Data (HEX)`; monospace CAN data; themed scrollbars; bounded view rendering contract for the future.

Counters: `Frames`, `Displayed`, `Dropped`. Initially all zero. Never initialize from unrelated sample logs or hardcode `16,644` from the screenshot.

Provide future-only interface methods such as `append_frame_batch(frames)`, `clear_display()`, `set_monitoring_state(state)`, `set_logging_state(state, path=None)`; these take typed view models and perform UI updates only. No RX thread and no raw bus in M03.

- `Clear` may clear locally shown data; it must not affect connected bus state.
- `Export CSV` should be disabled until actual data/export behavior is implemented (or connected to an existing proven exporter).
- `Start BLF Log` is an explicitly disabled placeholder with tooltip until real file logging is implemented; do not create empty/fake BLF files or falsely display REC.
- Distinguish real current state vs illustration: status must show `Not monitoring` in UI-only milestone.
- Future logging requirement is raw CAN frames including ISO-TP control frames, not reconstructed UDS strings; this milestone implements no logger.

## 11. Task M03-UI-07 — `.diag` import adapter and safe persistence

Implement only the minimum *UI data import* needed to populate real rows from `.diag`. Keep as pure code, away from widgets.

Verified sample schema:

```
{
  "Header": {"IDVehicle": 8, "Description": null},
  "TestCaseItem": [
    {
      "ECUObj": {"ECUName": "BCM", "IDReq": 1665, "IDResp": 1537,
                 "DLLFile": "VF5NP\\BCM\\VF5_SeednKey_BCM_NP.dll"},
      "TransMess": " 22 F1 90",
      "ExpectMess": " 62 F1 90",
      "DelayTime": 100,
      "RepeatTimes": 1,
      "Remark": null,
      "TransmitRule": {}, "ReceiveRule": {}
    }
  ]
}
```

Mapping into existing model:
- `ECUObj.ECUName` -> `DiagnosticStep.ecu`
- `TransMess` -> `request` (normalize spaces/case, validate HEX)
- `ExpectMess` -> `expected_response` (null -> empty)
- `DelayTime` -> `delay_ms`
- `RepeatTimes` -> `repeat`
- `Remark` -> `comment`
- source list order -> `step` from 1..N
- `sequence_name` from filename or an existing verified value; document the choice.
- `match` defaults to `prefix` for imported examples, explicitly described as a UI expectation and not a performed UDS comparison.

**DO NOT** take `.diag` `IDReq`, `IDResp` or `DLLFile` as canonical ECU config. Do not call the DLL. Do not process unknown/obfuscated JSON keys, `TransmitRule` or `ReceiveRule` as executable instructions; preserve source file unmodified. Perform robust JSON/type validation and show import errors.

The native V-CODE `DiagnosticSequenceRepository` owns `.json` read/write. For imported `.diag`, saving edits uses a clearly named **Save As `.json`** path or non-destructive sidecar if an existing project convention requires it. Never destructively rewrite the source file. Avoid claims of lossless round-trip of unsupported `.diag` fields.

## 12. Task M03-UI-08 — Save Order and UI preferences

- Copy the existing Coding Value **explicit Save Order** UX pattern for the sequence sidebar; do not copy its workspace storage or mutate files to reorder them.
- Persist saved sequence IDs/paths in separate CAN Interface UI preferences (prefer existing settings conventions if one exists). Use atomic temp-write-and-replace similar to `CodingWorkspaceStore.save()` when appropriate.
- Distinguish sequence sidebar order from diagnostic row `Step` order. Sequence order is a view preference; row order is part of `DiagnosticTestCase` and persists through normal Save.
- Reopening V-CODE restores sidebar order, last selected sequence and optional splitter positions when safe. If settings file missing/invalid, use safe defaults; do not crash.
- Editing comments or other row metadata must not silently save an unsaved manual sidebar reorder.
- Existing Coding Value Save Order behavior and data must remain untouched.

## 13. Task M03-UI-09 — Theming and visual fidelity

- Use `ThemeManager.fn_colors()`, `PrimaryTable`, `PrimaryButton`, `SecondaryButton`, `ActionButton`, `PrimaryComboBox`, `PrimaryLineEdit`, `PrimaryCheckBox`, `PrimaryLabel` as appropriate.
- Use `fn_apply_scrollbar_style()` for sidebar, table, monitor, any scroll area. Refresh both directions on theme change.
- Implement a compact themed row action button using existing button QSS conventions and a suitable smaller minimum size. Do not change global `PrimaryButton` width/height defaults, which would affect other tabs.
- Honor Light and Dark Mode; no hard-coded dark backgrounds copied from mockup. Use semantic SUCCESS/DANGER/WARNING and selection colors from theme.
- Avoid `PrimaryTable.fn_refresh_theme()` clobbering custom outcome styles; restore semantic status by item foreground/icons or post-refresh rendering.
- Preserve V-CODE spacing, rounded corners, Segoe UI where present, hover/disabled/pressed states, and existing scrollbar thickness.
- Avoid per-widget broad stylesheet selectors that leak into other tabs.
- Row-specific button alignment, table min height, stretch factors and horizontal scrolling must work at varying DPI/screen sizes.

## 14. Task M03-UI-10 — Signal contracts and data flow

Suggested top-level signals/contracts (adapt naming to project):

```
sequence_selected(document_id)
sequences_checked_changed(tuple[document_id, ...])
sequence_order_save_requested(tuple[document_id, ...])
row_selected(step_id)
row_send_requested(step_id)               # UI intent ONLY
selected_rows_changed(tuple[step_id, ...])
sequence_modified(test_case)
sequence_save_requested(test_case, path)
```

- Use immutable/stable logical identifiers for selection and actions where possible; Qt table index is not an immutable step identity when rows move.
- Child widgets must never directly call `CANService.fn_connect()`, `fn_send_frame()`, or raw bus APIs.
- Qt slots mutate only their designated presentation components.
- Prevent duplicate event connections during re-render/theme updates.
- Do not create circular imports between tab and child widgets.

## 15. Tests & acceptance

Add GUI/offscreen and pure importer tests; run all affected existing M01/M02/sequence regressions.

Required cases:
1. Correct left/top/bottom splitter hierarchy and responsive resizing.
2. Sidebar search/filter, checkbox selection versus active sequence, selected count.
3. Default numeric sequence ordering; drag order Save Order and persistence; unsaved order remains dirty.
4. Native `.json` sequences remain loadable; external `.diag` import reads 16 VIN steps with correct ECU, `22 F1 90`, `62 F1 90`.
5. Four referenced `.diag` schemas (or synthetic equivalents) handle null ExpectMess/Remark and leading spaces; unknown fields ignored safely.
6. Vehicle loaded from `VehicleService`; combo matches actual `Vehicle.ecus`; missing ECU warning; no duplicated ECU ID/DLL fields.
7. Table visible columns EXACTLY as approved; each `>` button targets correct logical row after insertion, deletion and sorting disabled.
8. Row checkboxes are independent of `>` clicks; selected row updates Current Test Case.
9. Comment edit persists via native sequence save; imported `.diag` is never overwritten.
10. Invalid HEX/Delay/Repeat shows correction/error without corrupting model.
11. No fake Receive Message, no fake Passed, no fake monitor frames, no fake BLF file.
12. M02 Connect/Disconnect/Discovery controls retain states and worker lifecycle.
13. Light/Dark refresh applies to all new widgets, buttons, tables, scrollbars, hover and disabled styles.
14. Layout remains usable at 1600×900, 1366×768, and higher DPI; no unusable fixed width.
15. Empty/no-vehicle/no-sequence/invalid-source cases.
16. Existing Diagnostic Sequence repository/table/list, Vehicle Manager, Coding Value Save Order and Log Analyze tests remain green.

Manual screenshot review: compare with supplied screenshot structure, NOT exact colors. Pay special attention to relative panel sizes and compact rows.

## 16. Deliverables, incremental implementation plan and reporting

Implement in this order, checkpoint tests after each:

- **UI-01 Shell:** independent widgets and splitter composition; M02 regressions.
- **UI-02 Sidebar:** search/checkbox/selected/open plus manual Save Order.
- **UI-03 Table:** exact columns, themed `>` action, validation, add/delete/edit/comment/save contracts.
- **UI-04 Vehicle binding + `.diag` importer:** model adapter, canonical ECU mapping and safe Save As.
- **UI-05 Bottom panels:** existing connection + read-only Current Test Case; monitor visual shell.
- **UI-06 Theme & QA:** styling, resize/DPI, tests and documentation.

Create `docs/can_interface/M03_UI_LAYOUT_REPORT.md` recording:
- Before/after module diagram
- All changed files and their responsibilities
- Existing controls/models/services reused
- Exact layout and splitter ratios
- `.diag`/`.json` compatibility rules
- Vehicle Manager mapping and missing ECU strategy
- Save Order versus sequence Save semantics
- What the `>` button does **during UI-only M03**
- What is NOT implemented (ISO-TP/UDS/CAN RX/BLF)
- Test commands/results and known limitations
- Handoff contracts for M04 transport and later sequence runner

**Final completion requirement:** The app launches, CAN Interface looks structurally like the approved screenshot in Light and Dark Mode, all sequence data and vehicle data bindings are real, every button has an honest action/status, and M01/M02 behavior remains intact. **Never claim that clicking `>` sends UDS or that BLF logging works yet.**
