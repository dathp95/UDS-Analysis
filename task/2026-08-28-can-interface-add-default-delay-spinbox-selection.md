# CAN Interface - Add Default Delay and Number Input Selection

## Request

Adjust CAN Interface Diagnostic Sequence UI behavior:

- First `+ Add` should create a row with `Loop = 1` and `Delay = 100`.
- After pressing Loop/Delay plus-minus buttons, the numeric text should not remain selected/highlighted.

## Changes

- Updated the empty-table Add inheritance fallback to use `DL (ms) = 100` and `Loop = 1`.
- Kept later Add behavior inheriting ECU, Delay, and Loop from the previous row.
- Updated `PrimaryNumberInput` so `stepUp()` and `stepDown()` clear the internal text selection and place the cursor at the end.
- Added regression tests for default first-row Delay/Loop and clearing selection after plus-minus actions.

## Verification

- `python -m unittest tests.gui.test_diagnostic_sequence_table` -> OK, 31 tests.
- `python -m unittest tests.gui.test_can_interface_tab tests.gui.test_diagnostic_sequence_table tests.gui.test_diagnostic_sequence_list` -> OK, 48 tests.
- `python -m py_compile ...` could not be run because the shell process helper failed, but the unittest run imported and executed the touched modules successfully.