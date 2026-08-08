# Task Summary: Preserve Input on Invalid Display Rules Import

Date: 2026-08-08

## Problem

When users entered invalid data in `Import Rules Display Names`, the app showed a warning popup, but the import dialog had already closed. Because the dialog closed, the pasted user data was lost and users could not edit the invalid input.

## Root Cause

`ImportDisplayNamesDialog` only validated that the text box was non-empty before calling `accept()`. Invalid rule formats were detected later in `VehicleManagerTab._on_import_display_rules_clicked()` by `import_display_name_rules(...)`, after the dialog had already closed.

## Change

- Added `validate_display_name_rules(rules_text)` in `core/config_loader.py`.
- Refactored rule parsing into `_parse_display_name_rules(...)` so validation and import share the same format checks.
- Updated `ImportDisplayNamesDialog._on_import_clicked()` to validate rule format before accepting the dialog.
- If validation fails, the warning popup is shown and the dialog remains open with the original user input intact.

## Verification

- `py_compile` passed for changed files.
- Focused tests passed: `Ran 12 tests ... OK`.
- Full unittest suite still has one unrelated pre-existing failure:
  - `test_vehicle_manager_has_display_names_import_button`
  - Current UI text: `Import File Display Names`
  - Test expectation: `Import Display Names`

## Files Changed

- `core/config_loader.py`
- `gui/dialogs/import_display_names_dialog.py`
- `tests/core/test_display_names_import.py`
- `tests/gui/test_vehicle_selector.py`
