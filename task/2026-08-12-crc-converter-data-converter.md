# CRC Converter data converter panel

## Yeu cau
Bo sung panel `Converter` ben phai tab `CRC_Converter` ho tro V1:
- Hexadecimal
- Decimal
- ASCII

## Thay doi
- Them `core/converter.py` voi API `convert_data(value, from_format, to_format)`.
- Ho tro chuyen doi HEX/DEC/ASCII theo tung byte.
- Validate invalid HEX, odd-length HEX, invalid decimal, decimal ngoai `0..255`, va From/To trung nhau.
- Them UI ben phai `CRC_Converter` gom From/To combobox, input/output multiline editor, `CONVERT`, `SWAP`, `CLEAR`, `Copy Result`.
- Dung `PrimaryLabel`, `PrimaryComboBox`, `PrimaryButton`, `ThemeManager`, va `fn_apply_scrollbar_style`.
- GUI chi doc input, doc From/To, goi converter, hien thi ket qua/loi.

## Verification
- `python -m unittest tests.core.test_converter tests.core.test_crc`
- `python -m unittest tests.gui.test_crc_converter_tab`
- `python -m py_compile core/converter.py gui/tabs/crc_converter_tab.py tests/core/test_converter.py tests/gui/test_crc_converter_tab.py gui/windows/main_window.py main.py`
- `python -m unittest tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_coding_value_tab_is_next_to_log_analyzer tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_crc_converter_tab_is_available_with_crc_panel`
- Khoi tao `MainWindow` offscreen voi mock `can/pandas`: `MainWindow OK`
