# CAN Interface UI Update - Execution Row Import Loop Delay

## Request

Adjust the CAN Interface diagnostic execution row order:

Vehicle [VF5NP] [+ADD] (Loop) (Delay) [Import]

The Import button must import both Loop and Delay values into the table rows. Loop and Delay numeric values should be centered inside their input boxes.

## Changes

- Reordered the Diagnostic Sequence execution row so Vehicle and + Add appear first, followed by Loop, Command Delay, Import, then EXPORT/STOP/RUN on the right.
- Changed the import button label to `Import`.
- Updated import behavior to apply both Loop and Command Delay values.
- Preserved selected-row behavior: selected rows are updated if any are selected; otherwise all rows are updated.
- Center-aligned the Loop and Command Delay number fields.
- Added/updated GUI tests for row order, centered number fields, and Loop/Delay import behavior.

## Verification

- `python -m unittest tests.gui.test_diagnostic_sequence_table`
- `python -m unittest tests.gui.test_can_interface_tab tests.gui.test_diagnostic_sequence_table tests.gui.test_diagnostic_sequence_list`
- `python -m py_compile main.py gui/widgets/controls/primary_number_input.py gui/widgets/diagnostic/diagnostic_sequence_table.py gui/tabs/can_interface_tab.py`

