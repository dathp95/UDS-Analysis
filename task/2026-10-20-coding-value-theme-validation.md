# Coding Value: theme refresh must not validate Raw Value

## Confirmed root cause

`shortcuts/shortcuts.json` maps Ctrl+B to `toggle_theme`. MainWindow's shortcut
action clicks `vehicle_manager_tab.theme_switch.switch_dark`. The switch emits
`theme_changed`, connected to `VehicleManagerTab.fn_change_theme`, which updates
ThemeManager and calls the top-level `MainWindow.fn_refresh_theme`.

The global refresh calls CodingValueTab even when Log Analyzer is active.
CodingValueTab refreshes its workspace sidebar and EVERY panel in
`_panel_by_workspace_id`, including hidden workspaces. Each CodingValuePanel
refreshes the group style, path/filter editors, action buttons, scrollbars and
its CodingValueTable. The sidebar refreshes its buttons, search and workspace
items. Table refresh delegates to PrimaryTable, refreshes decoded combo styling
and reapplies MATCH/No-M styling. No theme handler intentionally edits Raw Value.

The accidental data path is:
`CodingValueTable.fn_refresh_theme -> PrimaryTable.fn_refresh_theme ->
_refresh_row_colors -> QTableWidgetItem.setBackground -> itemChanged ->
CodingValueTable._handle_item_changed -> _apply_raw_value_to_row`.

`itemChanged` includes changes to presentation roles, not only edited text.
The handler only checks column 4 and `_syncing_raw_value`; it does not distinguish
recoloring from a user edit. Consequently each affected raw cell is validated
again. Blank or already invalid cells raise `QMessageBox.warning` with title
`Invalid Raw Value` at `_handle_item_changed`; valid cells unnecessarily emit
`raw_value_changed`, synchronize decoded values and can update payload/workspace
state. Multiple rows/workspaces and repeated refreshes multiply the dialogs.

The synthetic Byte 14 / BitLength 4 case reproduced six validator calls during
six alternating theme refreshes, plus data-change emissions on valid values
and false validation warnings for empty values. This is not a claim to have
inspected the user's original Coding dataset or inferred its exact bad payload.

## Fix

- `CodingValueTable.fn_refresh_theme`: scope `QSignalBlocker(self)` around ONLY
  presentation refresh, including base row colors and result colors. Scope
  `QSignalBlocker(combo)` around each decoded combo's style refresh. Original
  signal-block states are restored even when a child refresh raises.
- `MainWindow._setup_shortcuts`: wire only `toggle_theme` directly as a window-wide
  action. It previously went through the Log Analyzer-only guard, so Ctrl+B did
  not work with Coding Value active. All other shortcut actions keep that guard.
- Raw validation, edit handlers, payload conversion, bounds checks and warning
  messages are unchanged. No global popup suppression was added. Existing
  invalid values stay verbatim during theme changes; no clamp/truncation/repair.
  A real invalid edit still warns and restores the previous value as before.

Signal-blocker semantics were checked against the
[Qt documentation](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QSignalBlocker.html).

## Verification

- Six new deterministic offscreen Qt tests pass. They cover invalid FF, valid
  0F and blank raw values at Byte 14 / BitLength 4, repeated Dark/Light refresh,
  no validator/data-change signals during styling, MATCH/No-M colors, manual
  valid 0A and invalid 10 edits, and blocker restoration after a child exception.
- Actual QTest Ctrl+B events run four times with Log Analyzer active and four
  times with Coding Value active. Two workspace panels, raw/decoded values,
  row metadata, payload/baseline snapshots and temporary workspace files remain
  identical; no warning or dirty-state signal is emitted. The harness uses real
  shortcut, switch and refresh methods without application activation startup.
- Python syntax compilation and whitespace checks pass.
- An initial broad regression run was interrupted after RAM reached roughly
  1.5 GB and a fixture workspace PermissionError appeared. That run had failures
  and was not counted as a passing/full regression result. Verification was
  narrowed and rerun with the default workspace redirected to temporary files
  inside the repository. Full-suite validation remains a limitation.
- Two Coding Excel export tests fail unchanged on HEAD because they expect
  headers/style on row 1, where the existing generated-by banner now lives.
  Both failures were independently reproduced using HEAD exporter source in
  memory. No exporter/test expectation was changed for this fix.
- Isolated regression completed: 75 tests, 71 passed, three failures and one
  error. Besides the two exporter cases, the old Log Analyzer layout test asks
  for a missing `content_layout` attribute, and the old theme-switch layout test
  expects its widget in a different layout slot. Neither layout was changed.
  Both layout cases were also independently reproduced with HEAD MainWindow
  and CodingValueTable sources loaded in memory. All four are confirmed baseline
  failures/errors, not introduced by this patch.
- No manual desktop/hardware run was performed.

## Modified files/functions

- `gui/widgets/coding_value/coding_value_table.py`: `fn_refresh_theme` and import.
- `gui/windows/main_window.py`: `_setup_shortcuts`.
- `tests/gui/test_coding_value_theme_refresh.py`: new regression tests/harness.
- `task/2026-10-20-coding-value-theme-validation.md`: this report.

The existing change in `config/quick_filters.json` was preserved. No original
Coding configuration/dataset, log, licensing/RSA code or key file was modified.
No Git commit was created.
