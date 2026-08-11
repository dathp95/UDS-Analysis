# Coding Value Payload Preview Highlight

## Context
User wanted a second `QPlainTextEdit` under `txt_coding_value`.
It should display the same payload value as input, then update and highlight the affected byte when the user changes values in the table.

## Changes
- Added read-only `txt_coding_preview` under the Coding value input editor.
- Kept both payload editors limited to three visible lines with styled scrollbars.
- Added `raw_value_changed` signal from `CodingValueTable` when the user changes Raw value directly or via Decoded Value combobox.
- The panel now keeps a byte list for the preview payload and updates it when table Raw value changes.
- Byte-aligned fields replace whole bytes.
- Bit fields merge back into the original byte range using the row's Byte Pos, Bit Pos, and Bit Length.
- Updated byte positions are highlighted in the preview editor.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_payload_preview_updates_and_highlights_table_raw_changes` passed.
- `python -m unittest tests.gui.test_coding_value_tab` passed: 10 tests.
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts` passed: 16 tests.
- `python -m py_compile gui/widgets/coding_value/coding_value_panel.py gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py` passed.
- `python -m unittest discover` ran 53 tests and failed on existing missing environment dependencies: `cryptography` and `can`.