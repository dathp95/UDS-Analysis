# Coding Value Bitfield Encode

## Context
User wanted Coding value payload Encode to understand bit fields when rendering Raw value rows.
Example: payload byte 17 is `0x12`.
- `Bit Pos = 0`, `Bit Length = 4` should render `02`.
- `Bit Pos = 4`, `Bit Length = 4` should render `01`.

## Changes
- Updated Coding value table Encode logic to use `Byte Pos`, `Bit Pos`, and `Bit Length` together.
- Byte-aligned fields still render full bytes as before, for example `4A 39` for a 16-bit field at bit position 0.
- Non-byte-aligned fields are extracted using LSB-first bit numbering within the selected byte range, matching the user's `0x12` example.
- Added a regression test for byte 17 split into low/high nibble rows.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab` passed: 8 tests.
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts` passed: 14 tests.
- `python -m py_compile gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py` passed.