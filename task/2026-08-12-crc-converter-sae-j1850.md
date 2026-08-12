# CRC Converter SAE-J1850

## Yeu cau
Bo sung layout ben trai trong tab `CRC_Converter` de tinh `CRC8_SAE_J1850`.

## Thay doi
- Them `core/crc.py` de parse HEX input va tinh CRC-8/SAE-J1850 ngoai GUI.
- Cap nhat `gui/tabs/crc_converter_tab.py` voi label, input, nut `Calculate CRC`, va output read-only.
- GUI chap nhan upper/lowercase, space/newline/contiguous HEX thong qua parser core.
- Input invalid hoac odd-length HEX khong lam app crash, output duoc clear va tooltip bao loi.
- Them test core va GUI cho CRC Converter.
- Cap nhat test main window theo tab `CRC_Converter` da co panel CRC.

## Verification
- `python -m py_compile core/crc.py gui/tabs/crc_converter_tab.py gui/windows/main_window.py tests/core/test_crc.py tests/gui/test_crc_converter_tab.py tests/gui/test_main_window_shortcuts.py`
- `python -m unittest tests.core.test_crc tests.gui.test_crc_converter_tab tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_coding_value_tab_is_next_to_log_analyzer tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_crc_converter_tab_is_available_with_crc_panel`
