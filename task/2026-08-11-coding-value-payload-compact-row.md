# Coding Value Payload Compact Row

## Context
User wanted the Coding value payload editor and its three action buttons to be displayed on one row.
The payload editor should display at most three lines and use a scrollbar when content is longer.

## Changes
- Moved `txt_coding_value`, Encode, Copy, and Clear into one horizontal row.
- Limited `txt_coding_value` height to three text lines.
- Kept vertical scrollbar as needed and applied the existing scrollbar style.
- Added a GUI regression test to verify the compact row layout and styled scrollbar.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_payload_input_and_actions_share_one_compact_row` passed.
- `python -m unittest tests.gui.test_coding_value_tab` passed: 9 tests.
- `python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py` passed.