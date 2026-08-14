# Coding Value Filter Result

## Request
Allow `txt_parameter_filter` in the Coding Value tab to filter rows by the `Result` column in addition to the `Parameter` column.

## Changes
- Updated `CodingValueTable.filter_by_parameter()` to match text from both `Parameter` and `Result` columns.
- Added `_cell_text()` helper to safely read optional table columns.
- Added regression test for filtering `No-M` after CHECK results are visible.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_parameter_filter_matches_result_column_after_check tests.gui.test_coding_value_tab.CodingValueTabTests.test_check_button_adds_before_columns_and_compares_current_values tests.gui.test_coding_value_tab.CodingValueTabTests.test_result_header_click_does_not_reorder_table` passed.
- `python -m py_compile gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py` passed.
- Full `python -m unittest tests.gui.test_coding_value_tab` still has one unrelated existing failure: `cmb_coding_json.width()` is `300`, test expects `200`.
