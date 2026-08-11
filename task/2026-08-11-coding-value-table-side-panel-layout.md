# Coding Value Table Side Panel Layout

## Context
User wanted a layout on the right side of the Coding value table.
The side panel should have two vertical sections:
- Top section with four buttons: CHECK, EXPORT, COPY, CLEAR.
- Bottom section showing a working log for future byte-change history.
Only the layout is required in this step; button functions will be handled later.

## Changes
- Wrapped the table in `table_area`, a horizontal layout containing the table and a right-side panel.
- Added `table_side_panel` on the right side of the table.
- Added `table_action_panel` with vertical buttons:
  - `btn_check`
  - `btn_export`
  - `btn_table_copy`
  - `btn_table_clear`
- Added read-only `txt_working_log` below the action buttons with the existing scrollbar style.
- Added a GUI layout test for the new right-side panel.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_table_has_right_side_actions_and_working_log_layout` passed.
- `python -m unittest tests.gui.test_coding_value_tab` passed: 12 tests.
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts` passed: 18 tests.
- `python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py` passed.