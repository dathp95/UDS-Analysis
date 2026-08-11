# Coding Value Refresh Updates Raw Data

## Context
User wanted the preview Refresh button to also refresh table Raw value data exactly like pressing Encode.

## Changes
- Extracted shared payload encoding logic into `_encode_payload_to_table`.
- `Encode` now calls the shared helper with warning dialogs enabled.
- Preview `Refresh` now calls the same helper, so Raw value cells and decoded values are refreshed from `txt_coding_value` before the preview is rebuilt.
- If no table row can be updated, Refresh still rebuilds the preview from current input text.
- Fixed input/preview button ordering to match the intended left-side order:
  - Input: Encode, Copy, Clear
  - Preview: Refresh, Copy, Clear
- Updated the Refresh test to assert table Raw value changes from `08` to `99` after Refresh.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_payload_preview_refresh_copy_and_clear_buttons` passed.
- `python -m unittest tests.gui.test_coding_value_tab` passed: 11 tests.
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts` passed: 17 tests.
- `python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py` passed.