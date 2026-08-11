# Coding Value CHECK working log

## Yeu cau
Khi user bam CHECK, working log can hien thi tong so No-M, danh sach byte thay doi voi decoded value before/after, va CRC before/after.

## Thay doi
- Luu baseline payload bytes khi set preview/encode de co CRC before.
- Sau CHECK, render working log tu cac row co Result = No-M.
- CRC before/after hien lay theo byte cuoi cua payload baseline/preview.
- Them regression test cho case doi coding byte va CRC byte.

## Verification
- python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_check_button_writes_working_log_for_no_match_changes_and_crc
- python -m unittest tests.gui.test_coding_value_tab
- python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts
- python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py