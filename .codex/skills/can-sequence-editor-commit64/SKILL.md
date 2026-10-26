---
name: can-sequence-editor-commit64
description: Implement CAN Interface Commit 64: unsaved ECU drafts, sequence editor TSV import/export, fixed footer actions in CanSequenceSidebar.
---

# V-CODE CAN Interface — Commit 64 (REVISED)

## Baseline and scope
- Repository `dathp95/UDS-Analysis`, baseline commit 63 `37e0f1be3310b7981574b84554483a6cf8107948`.
- Preserve Vector connection ownership, ISO-TP, UDS manual send policy, CAN Monitor, BLF, portable per-Vehicle/ECU DLL store, Step ID/runtime result isolation, and .diag read-only source handling.
- No live SecurityAccess, no native DLL execution, no automatic Run Selected.
- Do not commit or push automatically.

## REQUIRED UI placement — most important revision
- ALL five sequence action buttons belong **inside `gui/widgets/can_interface/sequence_sidebar.py` / `CanSequenceSidebar`**, below the scrolling sequence list — **not** in the diagnostic table header, not in CAN tab footer, and not in a separate dialog-only toolbar.
- Order exactly: `+ Add | Import SEQ | Export SEQ | Save | Save Order`.
- Sidebar is narrow (roughly 380 px in provided screenshot). Use a responsive **fixed footer** with two compact rows if five buttons do not fit in one row without clipping. Example row 1: `+ Add | Import SEQ | Export SEQ`; row 2: `Save | Save Order`. Preserve the visual/read order above. Do not grow sidebar width to force a single row.
- Match existing `PrimaryButton`, `SecondaryButton` themes; Save should be primary when the document is dirty; Save Order independently enabled only on order changes. Inherit button size/spacing conventions; do not use custom unthemed raw QPushButton.
- Structure: header/title → search → Select All (visible) → scrollable list with stretch factor 1 → compact error/selected count or status area (bounded height) → **fixed footer action area**. Sidebar footer does not scroll when list scrolls and remains visible at 1366x768, 1600x900, Light/Dark, minimum supported window size. Error reporting must never push footer off screen; use a compact bounded status area with tooltip/details on demand.
- Retain `CanSequenceSidebar`'s `QListWidget` and checkbox-click/drag reorder behavior; DO NOT replace list items with buttons unless necessary. Apply existing `fn_apply_scrollbar_style()` on the `QListWidget` vertical scrollbar; reference `gui/widgets/coding_value/ecu_workspace_sidebar.py` (scroll area/fixed footer, dirty asterisk) and `gui/widgets/log_analyzer/quick_access.py` (scrollbars, themed compact footer and action patterns). Do NOT duplicate the `addWidget()` pattern present in coding sidebar. Avoid nested scrolling.
- Keep `Save Order *` only for order edits; do not let saving document silently save pending reordering.
- Fix `fn_refresh_theme()` to theme all newly introduced buttons and scrollbar while preserving list selection, checked state, scroll position when feasible, and drag state.

## A. Vehicle Manager unsaved ECU drafts
1. In `gui/tabs/vehicle_manager_tab.py`, snapshot draft for **each (Vehicle name, ECU name)** before switching selection. Capture `ECUInfoWidget` basic fields, `ECUResourceWidget` fields, chosen DLL path, and explicit Browse/import intent (`_browsed_dll`), not just saved ECU.
2. On returning to EPS after browsing DLL without Save, show exact draft DLL path and preserve intended import. Save must import via existing Commit 63 storage transaction.
3. Switching ECU/Vehicle must not implicitly write JSON or copy DLL; saved model remains the source for CAN Interface until Save succeeds.
4. On Save success, clear only that ECU draft and dirty marker; on failure retain draft. On explicit Discard, discard only intended draft. Guard rename/delete and switching with clearly documented behavior. A draft from one Vehicle/ECU may never leak into another.
5. Add regression test Browse EPS → BCM → EPS → Save → reload; test errors, multiple drafts, theme and portable storage.

## B. Import unknown ECU naming
- When importing a `.json`, `.diag`, or pasted sequence, validate ECU names against the currently chosen Vehicle's ECU configuration.
- Unmatched ECU text shall appear as an **empty ECU selector field**, not `⚠ name` or a placeholder carrying invalid name. Do not invent a CAN target. No send when unresolved.
- Preserve unmatched original names in an import summary/diagnostic report, separate from valid saved ECU fields; avoid silently losing diagnostics when loading existing editable documents. Consider a reversible, non-mutating display state for existing files until user explicitly saves normalized data.
- Handle unavailable/no selected Vehicle without silently emptying every ECU. Do not make unrelated ECUs appear invalid because Vehicle has not been selected.
- Add tests for known, unknown, blank ECU; changing Vehicle; unsupported character names; missing vehicle; no unintended TX.

## C. Diagnostic table schema and column
- Restore editable `DiagnosticStep.sequence_name` column between **Step** and **ECU** in `gui/widgets/can_interface/diagnostic_table_panel.py` and any base `DiagnosticSequenceTable` mapping required.
- Keep checkbox and manual send `>` columns even though the clipboard exchange schema omits them. Maintain correct column constants/offsets for editors, cell handlers, themes, Copy, result rendering, and row action.
- Changes to `sequence_name` mark document dirty but do not erase results from other steps. Preserve Step IDs.
- Table header title and active `CanSequenceSidebar` item show ` *` for dirty document. Clear only after successful Save. Dirty order remains separate (`Save Order *`).

## D. Sequence actions — all triggered from sidebar footer
- `+ Add`: create a new native JSON sequence draft, prompt for a distinct name, activate it without writing until user clicks Save. Do not overwrite a duplicate; respect Save/Discard/Cancel on switching existing dirty document.
- `Import SEQ`: open a dialog for pasted TSV text (allow CSV where correctly quoted), preview before applying, and append or replace only through an explicit mode choice. Input columns EXACTLY:
  `Step | Test sequence name | ECU | Payload(HEX) | Delay(ms) | Repeat | Expected Response (HEX) | Results | Comment`
  Preserve quoted comments/tabs where possible, validate row lengths, HEX formatting, delay/repeat, ECU mapping, and report errors with source row numbers. Do not partially mutate sequence on validation failure. Runtime `Results` is informational on import; **never** resurrect fake Passed status from imported data. Save after importing writes native `.json` as existing repo does.
- `Export SEQ`: export active sequence table to deterministic TSV with that exact nine-column order; use currently visible Results for rows with actual runtime; unrun rows blank/`—` consistently. Show modal preview dialog with **Cancel | Copy**, Copy copies the complete TSV to clipboard, no arbitrary filesystem write. Must reflect unsaved table values.
- `Save`: use existing `CanWorkspaceController.save_sequence()` and its `.diag` → Save As JSON semantics; do not permit overwriting `.diag` source. Place trigger in sidebar, keep old header Save only if needed for compatibility but avoid duplicated visible actions (prefer hide/remove redundant Save header). Save button is disabled unless document exists and is dirty or a newly created unsaved sequence. Existing save logic may need separate dirty-aware enablement.
- `Save Order`: retains existing `CanSequenceSidebar._save_order()` logic, independent order store; drag/drop still works with filtering disabled.
- Use new sidebar signals wired through `CanWorkspaceController` for add/import/export/save; do not create a second persistence mechanism.

## E. Duplicate entries and error/status UX
- Sidebar display names may duplicate; identity uses absolute source IDs / stable unique document identity, not text.
- For invalid `.json` / `.diag`, show informative errors in a **bounded** scrollable/detail area (or truncated label with tooltip), leaving action footer visible. Do not delete or overwrite malformed source files.
- Preserve search, visible checkbox selection, keyboard activation, drag order and Commit 59 deleted-QListWidgetItem regression fix. Before synchronous signals refresh the list, snapshot item data and do not use deleted C++ items.

## F. Regression and acceptance
- Mandatory tests: draft EPS DLL retention on switch; per-Vehicle isolation; imported unknown ECU blank; visible editable sequence name; five footer buttons fixed during long list scrolling and error overflow; Copy dialog headers/order; import validation atomic; JSON Save clears `*`; Save Order independent; `.diag` Save As; rejected dirty-document switch; selected/checked state; Qt object lifetime bug; preserved prior response Steps 1–4 after unrelated Step 5 edit; existing CAN/UDS/ISO-TP/BLF and DLL portable suites.
- Visually inspect Light/Dark 1366x768 and 1600x900: sidebar width approximately screenshot, footer always visible; no horizontal scrollbar or clipped label/button; scroll list does not scroll footer.
- Run focused and broader regression suites, record exact pass/fail/skip counts. Write `docs/can_interface/COMMIT64_SEQUENCE_EDITOR_DRAFTS_REPORT.md` with architecture, UX screenshots/test descriptions, migration notes and remaining risks.
- Do not change unrelated tabs or core CAN TX implementations. No auto commit or push.

## Suggested commit name
`can interface - commit 64: Preserve ECU Drafts and Enhance Sequence Sidebar Editor`
