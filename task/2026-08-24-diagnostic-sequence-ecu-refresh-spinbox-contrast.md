# Diagnostic Sequence ECU Refresh + SpinBox Contrast

## Summary

- Updated `PrimarySpinBox` stylesheet so spin buttons and arrows use ThemeManager tokens with stronger contrast, hover, pressed, and disabled states.
- Updated Diagnostic Sequence table ECU comboboxes to load ECU options from the selected Vehicle Package through `VehicleService.load_vehicle()`.
- Added `fn_set_vehicle(vehicle)` as a public API for refreshing table ECU options without direct JSON access.
- Preserved step ECU values when the selected vehicle does not contain that ECU; the combobox is visually unselected and the model remains unchanged.
- Updated `+ Add` so a new row is inserted after the selected row and inherits only the ECU from the row directly above it.
- Empty table add uses an empty ECU; missing inherited ECU remains in the model with an unselected combo.

## Verification

- `python -m unittest tests.gui.test_diagnostic_sequence_table` passed: 26 tests.
- `python -m py_compile main.py gui/widgets/diagnostic/diagnostic_sequence_table.py gui/themes/styles/controls/spinbox_style.py gui/widgets/controls/primary_spinbox.py gui/widgets/vehicle_manager/vehicle_selector.py` passed.
- `git diff --check` passed with only LF/CRLF warnings from Git on Windows.

## Notes

- No CAN/UDS execution logic was implemented or modified.
- `tests.gui.test_vehicle_selector` still has an unrelated existing failure for the Vehicle Manager display names import button text: expected `Import Display Names`, actual `Import File Display Names`.