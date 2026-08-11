# Coding Value export report

## Yeu cau
Nut EXPORT trong tab Coding Value can export toan bo phan dang hien thi cua table ra Excel trong folder report/date. File co ten EEIV_report_Coding value_datetime.xlsx va sheet co ten Coding value_<3 byte dau payload encode>, vi du Coding value_62 F1 08.

## Thay doi
- Connect btn_export voi export_coding_value().
- Tao workbook bang openpyxl, sheet name lay tu 3 byte dau cua encoded payload.
- Export headers va tat ca row/cell dang hien thi trong table, bao gom gia tri hien tai cua combobox Decoded Value.
- Tao folder ngay duoi REPORT_DIR va hien popup thong bao duong dan file sau khi save.
- Them regression test mo file Excel da export de kiem tra file, sheet, header va data.

## Verification
- python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_export_button_writes_visible_table_to_coding_value_report
- python -m py_compile gui/widgets/coding_value/coding_value_panel.py gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py
- python -m unittest tests.gui.test_coding_value_tab
- python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts