# Diagnostic Sequence Execution Row + Status Text Fix

Date: 2026-08-24

## Scope

Updated the CAN Interface diagnostic sequence center panel layout. No CAN/UDS execution logic, JSON schema, repository, or CAN backend changes were made.

## Changes

- Removed Duration UI from `DiagnosticSequenceTable`.
- Added `EXPORT`, `STOP`, and `RUN` buttons to the execution row using `PrimaryButton`.
- Kept Loop and Command Delay left aligned, with one stretch before the action buttons.
- Updated CAN connection status text to plain state text: `Disconnected`, `Connecting`, `Connected`, `Error`.
- Updated UI tests for the new execution row and status text.

## Verification

- `python -m unittest tests.repositories.test_diagnostic_sequence_repository tests.gui.test_diagnostic_sequence_list tests.gui.test_diagnostic_sequence_table tests.gui.test_can_interface_tab tests.test_main_startup`
- `python -m py_compile gui\\widgets\\diagnostic\\diagnostic_sequence_table.py gui\\tabs\\can_interface_tab.py tests\\gui\\test_diagnostic_sequence_table.py tests\\gui\\test_can_interface_tab.py`
- `git diff --check`

All listed checks passed.
