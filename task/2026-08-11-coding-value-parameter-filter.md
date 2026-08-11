# Coding Value parameter filter

## Yeu cau
Them mot thanh filter ngay tren table trong tab Coding Value de tim kiem theo Parameter.

## Thay doi
- Them PrimaryLineEdit txt_parameter_filter va filter_row ngay tren table.
- Connect textChanged cua filter voi filter_parameter_table().
- Them CodingValueTable.filter_by_parameter() de an/hien row theo cot Parameter, khong xoa data table.
- Sau import Excel se ap dung lai filter hien tai.
- Export Coding Value bo qua row dang bi an de file Excel dung voi table dang hien thi.
- Them regression test kiem tra filter case-insensitive, clear filter hien lai row va clear selection.

## Verification
- python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_parameter_filter_hides_non_matching_rows
- python -m py_compile gui/widgets/coding_value/coding_value_panel.py gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py
- python -m unittest tests.gui.test_coding_value_tab
- python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts