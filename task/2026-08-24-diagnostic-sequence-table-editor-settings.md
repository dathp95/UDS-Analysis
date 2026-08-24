# Diagnostic Sequence Table Editor + Execution Settings

Date: 2026-08-24

## Scope

Implemented Task 3 for the CAN Interface tab. This task only adds the diagnostic sequence editor foundation and does not implement CAN/UDS execution, ISO-TP, RUN, STOP, or reports.

## Changes

- Extended `DiagnosticTestCase` with execution settings via `DiagnosticExecutionSettings`.
- Added backward-compatible JSON support for the optional `execution` object.
- Preserved old JSON files without `execution` by loading defaults: loop `1`, command delay `100` ms.
- Supported `step.delay_ms = null` as a blank per-step delay override.
- Added `DiagnosticSequenceTable` center editor with:
  - Execution settings row: Loop, Command Delay, Duration.
  - Sequence steps table with editable request, delay, repeat, expected response, comment, ECU combobox, and read-only receive/result columns.
  - In-memory model updates and dirty tracking through `sequence_modified`.
  - Safe validation for loop, command delay, repeat, delay, and HEX fields.
  - Prepared APIs: `fn_add_step`, `fn_remove_selected_step`, `fn_move_step_up`, `fn_move_step_down`.
- Integrated `DiagnosticSequenceList.sequence_selected` into `CANInterfaceTab` so selected sequences load into the center editor.

## Verification

- `python -m unittest tests.repositories.test_diagnostic_sequence_repository tests.gui.test_diagnostic_sequence_list tests.gui.test_diagnostic_sequence_table tests.gui.test_can_interface_tab`
- `python -m py_compile core\\diagnostic_sequence.py repositories\\diagnostic_sequence_repository.py gui\\widgets\\diagnostic\\diagnostic_sequence_table.py gui\\widgets\\diagnostic\\diagnostic_sequence_list.py gui\\tabs\\can_interface_tab.py`
- `python -m unittest tests.test_main_startup`

All listed checks passed.
