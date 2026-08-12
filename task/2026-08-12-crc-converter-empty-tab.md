# CRC Converter empty tab

## Yeu cau
Tao tab moi ten `CRC_Converter` nam sau tab `Coding value`.

## Thay doi
- Tao `gui/tabs/crc_converter_tab.py` voi class `CRCConverterTab` va layout rong.
- Them `crc_converter_tab` vao `MainWindow`.
- Chen tab `CRC_Converter` sau `Coding value`, truoc `Vehicle Manager`.
- Cap nhat test tab order va test widget rong.

## Verification
- `python -m py_compile gui/windows/main_window.py gui/tabs/crc_converter_tab.py tests/gui/test_main_window_shortcuts.py`
- `python -m unittest tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_coding_value_tab_is_next_to_log_analyzer tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_crc_converter_tab_starts_empty_with_base_layout`
- `python -m unittest tests.gui.test_main_window_shortcuts` hien con fail o test License & Support do expectation text `continued development` khong khop voi UI hien tai `Enjoying the tool? Buy me a coffee!`, ngoai scope task nay.
