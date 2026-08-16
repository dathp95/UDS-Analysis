# Transfer CRC Preview Offset Fix

## Request
Fix CRC_Converter -> Transfer CRC so the calculated CRC is written to the correct CRC byte in Coding Value preview. The previous behavior could write the value 3 bytes before the real CRC position when the preview includes the 3-byte UDS header.

## Root Cause
`fn_set_crc_value()` updated the table raw value by parameter and allowed the table raw-value signal to update the payload preview using the row byte position directly. For CRC rows whose Byte Pos is relative to data payload, the preview payload also contains the first 3 response bytes, causing a 3-byte offset error.

## Changes
- Added table helpers to find a row by parameter, read row payload location, and set raw value with optional raw-change signal emission.
- Updated Transfer CRC flow to set the CRC raw value without the generic preview signal, then update the preview at `byte_pos + 3` when the preview has a 3-byte header.
- Added a regression test where CRC row Byte Pos is 63 and preview length is 67, ensuring byte 66 is updated while byte 63 remains unchanged.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_set_crc_value_updates_crc_parameter_row tests.gui.test_coding_value_tab.CodingValueTabTests.test_set_crc_value_offsets_data_byte_pos_for_preview_header tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_crc_transfer_signal_updates_coding_value_tab`
- `python -m py_compile gui\widgets\coding_value\coding_value_panel.py gui\widgets\coding_value\coding_value_table.py tests\gui\test_coding_value_tab.py`

## Note
Full `tests.gui.test_coding_value_tab` still has unrelated layout expectation failures for combobox/filter/action row sizing/order.