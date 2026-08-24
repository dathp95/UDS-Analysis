# Diagnostic Sequence Table Cleanup + Add Row + Import Delay

Date: 2026-08-24

## Scope

Updated the Diagnostic Sequence editor table and execution row. No CAN/UDS execution, ISO-TP runtime, CAN backend, JSON storage, or DiagnosticSequenceRepository changes were made.

## Changes

- Removed the `Index` column from the Diagnostic Sequence table.
- Renamed table headers to the compact format: `Step`, `Test Sequence Name`, `ECU`, `TX Message`, `DL (ms)`, `Loop`, `EX Message`, `RX Message`, `Result`.
- Increased diagnostic table row height to `34` px using a single `ROW_HEIGHT` constant.
- Enabled multi-row selection for Import Delay while preserving row selection behavior.
- Added `Import Delay` button beside Command Delay.
- Added `+ Add` button beside Import Delay.
- Implemented `fn_add_step_after_selected()`:
  - inserts after the selected row
  - appends when no row is selected
  - creates a default `DiagnosticStep`
  - reindexes step numbers
  - selects the new row
  - marks the sequence dirty
- Implemented `fn_import_command_delay_to_rows()`:
  - applies current global Command Delay to selected rows
  - applies to all rows when no rows are selected
  - updates both table cells and in-memory model
  - marks the sequence dirty
- Improved `PrimarySpinBox` arrow-button styling using centralized ThemeManager colors.

## Verification

- `python -m unittest tests.repositories.test_diagnostic_sequence_repository tests.gui.test_diagnostic_sequence_list tests.gui.test_diagnostic_sequence_table tests.gui.test_can_interface_tab tests.test_main_startup`
- `python -m py_compile gui\\widgets\\diagnostic\\diagnostic_sequence_table.py gui\\themes\\styles\\controls\\spinbox_style.py gui\\widgets\\controls\\primary_spinbox.py tests\\gui\\test_diagnostic_sequence_table.py gui\\tabs\\can_interface_tab.py`
- `git diff --check`

All listed checks passed.
