# Coding Value Preview Action Layout

## Context
User wanted to rearrange the Coding value payload layout:
- Move Encode, Copy, Clear to the left of `txt_coding_value`.
- Add Refresh, Copy, Clear to the left of `txt_coding_preview`.
- Refresh should rebuild preview from the current input payload.
- Preview Clear should leave preview blank.

## Changes
- Replaced the previous payload button layout with two horizontal rows.
- Input row order: Encode, Copy, Clear, `txt_coding_value`.
- Preview row order: Refresh, Copy, Clear, `txt_coding_preview`.
- Added preview action methods:
  - `refresh_coding_preview`
  - `copy_coding_preview`
  - `clear_coding_preview`
- Kept the existing three-line editor height and styled scrollbars.
- Added tests for the new row order and preview button behavior.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_payload_input_and_actions_share_one_compact_row tests.gui.test_coding_value_tab.CodingValueTabTests.test_payload_preview_refresh_copy_and_clear_buttons` passed.
- `python -m unittest tests.gui.test_coding_value_tab` passed: 11 tests.
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts` passed: 17 tests.
- `python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py` passed.