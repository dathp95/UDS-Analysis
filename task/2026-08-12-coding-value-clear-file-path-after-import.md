# Coding Value clear file path after import

## Yeu cau
Sau khi user browse chon file Excel va bam Import trong tab Coding value, data hien thi trong combobox/table va o `file_path` tro ve rong.

## Thay doi
- Them `self.file_path.clear()` sau khi import Excel thanh cong, refresh combobox JSON va load table tu JSON.
- Cap nhat test `test_import_coding_excel_refreshes_json_drop_list_and_loads_table_from_json` de verify `file_path` rong sau import.
- Khong thay doi flow import selected JSON khi `file_path` da rong.

## Verification
- RED: `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_import_coding_excel_refreshes_json_drop_list_and_loads_table_from_json`
- GREEN: `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_import_coding_excel_refreshes_json_drop_list_and_loads_table_from_json`
- `python -m unittest tests.gui.test_coding_value_tab`
- `python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py`
