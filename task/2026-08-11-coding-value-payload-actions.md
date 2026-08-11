# Coding Value Payload Actions

## Context
User wanted the Coding value payload input to include three actions:
- Encode: apply bytes from the pasted payload into table Raw value cells by Byte Pos.
- Copy: copy the current payload text.
- Clear: clear the payload input.

Example byte mapping is zero-based:
- `62` maps to byte `0`
- `F1` maps to byte `1`
- `08` maps to byte `2`

## Changes
- Added Encode, Copy, and Clear buttons below the Coding value payload input.
- Encode parses two-hex-digit payload bytes and updates table Raw value by each row's Byte Pos.
- Rows with Bit Length greater than 8 consume multiple payload bytes and render them as `XX XX`.
- Copy writes the payload text to the application clipboard.
- Clear empties only the payload input.
- Kept corrected 4-bit behavior: multi-token values such as `08 09` are valid, while tokens outside a 4-bit nibble such as `10 09` are invalid.

## Verification
- `python -m py_compile core/coding_value.py gui/widgets/coding_value/coding_value_panel.py gui/widgets/coding_value/coding_value_table.py tests/core/test_coding_value_excel.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.gui.test_coding_value_tab`
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts`
- `python -m unittest discover` was also run. It found 50 tests but failed on existing missing environment dependencies: `cryptography` and `can`.
