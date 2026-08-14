# Coding Value Result Header Cleanup

## Request
Remove the previous Result-header click-to-sort approach from the Coding Value table and clean related code.

## Changes
- Removed custom Result header sorting behavior from `CodingValueTable`.
- Removed sort state, original-order tracking, row snapshot/reorder helpers, and header click signal connection.
- Restored table raw-value copy to use the current table row order, since Result sorting is no longer supported.
- Removed obsolete sort/copy-after-sort tests.
- Added a guard test that clicking the Result header does not reorder rows.

## Verification
- `rg` confirmed no remaining Result-sort symbols such as `RESULT_COLUMN`, `_handle_header_clicked`, `_reorder_rows`, `original_order`, or `fn_row_indexes_by_original_order`.
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_result_header_click_does_not_reorder_table tests.gui.test_coding_value_tab.CodingValueTabTests.test_table_copy_button_copies_raw_values_and_shows_timed_message tests.gui.test_coding_value_tab.CodingValueTabTests.test_check_button_adds_before_columns_and_compares_current_values` passed.
- `python -m py_compile gui/widgets/coding_value/coding_value_table.py gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py` passed.
- Full `python -m unittest tests.gui.test_coding_value_tab` still has one unrelated existing failure: `cmb_coding_json.width()` is `300`, test expects `200`.
