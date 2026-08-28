# CAN Interface SpinBox +/- and Select All Checkmark

## Summary

- Updated reusable `PrimarySpinBox` to use Qt `PlusMinus` button symbols, so Loop and Command Delay controls show `+` and `-` buttons.
- Updated Diagnostic Sequence `Select All` checkbox text to show a visible checkmark when selected and return to plain text when unchecked.
- Kept the change scoped to UI state only; no CAN/UDS execution logic was added or modified.

## Verification

- `python -m unittest tests.gui.test_diagnostic_sequence_table tests.gui.test_diagnostic_sequence_list` passed: 36 tests.
- `python -m py_compile main.py gui/widgets/controls/primary_spinbox.py gui/widgets/diagnostic/diagnostic_sequence_list.py gui/widgets/diagnostic/diagnostic_sequence_table.py gui/tabs/can_interface_tab.py` passed.
- `git diff --check` passed with only LF/CRLF warnings from Git on Windows.