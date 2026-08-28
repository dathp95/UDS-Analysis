# CAN Interface Custom Number Input

## Summary

- Added reusable `PrimaryNumberInput` with custom `-` and `+` `PrimaryButton` controls around an internal `PrimarySpinBox`.
- Hid the internal native spinbox buttons with `QAbstractSpinBox.NoButtons` for the Diagnostic Sequence Loop and Command Delay controls.
- Updated Diagnostic Sequence execution controls to use `PrimaryNumberInput` while preserving the existing `valueChanged(int)` model update behavior.
- Kept manual numeric entry, min/max validation, single-step behavior, and theme refresh support.
- Preserved the Select All checkmark behavior from the previous UI update.

## Verification

- `python -m unittest tests.gui.test_can_interface_tab tests.gui.test_diagnostic_sequence_table tests.gui.test_diagnostic_sequence_list` passed: 44 tests.
- `python -m py_compile main.py gui/widgets/controls/primary_number_input.py gui/widgets/controls/primary_spinbox.py gui/widgets/diagnostic/diagnostic_sequence_table.py gui/widgets/diagnostic/diagnostic_sequence_list.py gui/tabs/can_interface_tab.py` passed.

## Notes

- No CAN/UDS execution logic was implemented or modified.