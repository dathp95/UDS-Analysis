# Coding Value working log format

## Yeu cau
Doi format working log sau CHECK sang dang:
Total No-M: n

Changes: Decode value before -> after

Byte X: before -> after

CRC: before -> after

## Thay doi
- Doi format tung dong change thanh `Byte X: before -> after`.
- Doi header Changes thanh `Changes: Decode value before -> after`.
- Doi CRC thanh `CRC: before -> after`.
- Cap nhat regression test theo format moi voi nhieu byte thay doi.

## Verification
- python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_check_button_writes_working_log_for_no_match_changes_and_crc
- python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py
- python -m unittest tests.gui.test_coding_value_tab
- python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts