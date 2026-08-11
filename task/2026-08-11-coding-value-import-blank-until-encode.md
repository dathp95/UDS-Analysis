# Coding Value import blank until encode

## Yeu cau
Sau khi Browse/Import file Excel, table chi hien thi structure. Cot Raw value va Decoded Value de rong, chi cap nhat sau khi user Encode payload.

## Thay doi
- CodingValuePanel import Excel voi payload rong, khong tao preview/baseline tu input payload.
- CodingValueTable set_rows dat Raw value va baseline raw rong khi render import.
- Combobox Decoded Value khong auto-select decoded value luc import.
- Cap nhat GUI tests sang flow import -> encode moi co raw/decoded.

## Verification
- python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_import_coding_excel_renders_table_with_decoded_combobox
- python -m unittest tests.gui.test_coding_value_tab
- python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts
- python -m py_compile core/coding_value.py gui/widgets/coding_value/coding_value_table.py gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py