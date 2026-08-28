# CAN Interface - Add Row Inheritance and Delete Row

## Request

Update the CAN Interface Diagnostic Sequence table:

- When pressing `+ Add`, the new row should inherit ECU, Delay, and Loop from the previous row.
- When pressing the keyboard `Delete` key, delete the selected row.

## Changes

- `+ Add` now inherits:
  - ECU
  - `DL (ms)`
  - `Loop`
- Empty-table Add behavior still creates a blank ECU row with default Delay/Loop values.
- Added table key handling for `Delete`.
- `Delete` removes the selected row(s), reloads the table, reindexes Step values, selects the next available row, and marks the sequence as dirty.
- Kept the behavior inside `DiagnosticSequenceTable`; no CAN backend, UDS runtime, or JSON repository logic was changed.

## Verification

- `python -m unittest tests.gui.test_diagnostic_sequence_table`
- `python -m unittest tests.gui.test_can_interface_tab tests.gui.test_diagnostic_sequence_table tests.gui.test_diagnostic_sequence_list`

