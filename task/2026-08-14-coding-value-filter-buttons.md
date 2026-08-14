# Coding Value Filter Buttons

## Request
Redesign the `txt_parameter_filter` row in Coding Value to add two buttons: a No-M filter button and a Refresh filter button. Buttons must have controlled sizes and disabled states when there is no data.

## Changes
- Added `btn_filter_no_m` next to `txt_parameter_filter`, fixed width equal to the Result column width.
- Added `btn_refresh_filter`, fixed width 110 to match CHECK/EXPORT button sizing.
- Added `filter_no_match_rows()` to set the filter text to `No-M`.
- Added `refresh_parameter_filter()` to clear the filter and show all rows.
- Updated button states: both disabled when there is no table data; No-M remains disabled until CHECK results exist.
- Refreshed theme for the new buttons.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_filter_buttons_start_disabled_without_table_data tests.gui.test_coding_value_tab.CodingValueTabTests.test_action_buttons_require_payload_data_after_import tests.gui.test_coding_value_tab.CodingValueTabTests.test_parameter_filter_hides_non_matching_rows tests.gui.test_coding_value_tab.CodingValueTabTests.test_filter_no_match_and_refresh_buttons_update_filter tests.gui.test_coding_value_tab.CodingValueTabTests.test_parameter_filter_matches_result_column_after_check` passed.
- `python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py` passed.
- Full `python -m unittest tests.gui.test_coding_value_tab` still has one unrelated existing failure: `cmb_coding_json.width()` is `300`, test expects `200`.

## Layout Refinement
- `txt_parameter_filter` now fills the same horizontal region as the table.
- The right-side filter action area is fixed at 220 px to mirror the table side panel width.
- `No-M` and `Refresh` share that action area equally.

## Refinement Verification
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_parameter_filter_hides_non_matching_rows tests.gui.test_coding_value_tab.CodingValueTabTests.test_filter_no_match_and_refresh_buttons_update_filter tests.gui.test_coding_value_tab.CodingValueTabTests.test_filter_buttons_start_disabled_without_table_data` passed.
- `python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py` passed.
