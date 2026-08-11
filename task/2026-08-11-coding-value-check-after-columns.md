# Coding Value CHECK after columns

## Yeu cau
Khi user nhan nut CHECK trong tab Coding value, table can bo sung 3 cot ket qua:
- Raw value (after)
- Decoded Value (after)
- Result

Result hien thi MATCH neu raw value ban dau va raw value hien tai giong nhau, hien thi No-M neu khac nhau.

## Thay doi
- Them logic `apply_check_results()` trong `CodingValueTable` de tao/cap nhat 3 cot after.
- Luu `original_raw` khi import/set row va reset baseline khi Encode payload de co gia tri truoc khi user sua.
- Ket noi nut `CHECK` trong `CodingValuePanel` voi logic check table.
- Reset table ve 6 cot goc khi import lai du lieu moi de khong giu cot after cu.
- Bo sung regression test cho hanh vi bam CHECK, so sanh MATCH/No-M, dam bao bam CHECK nhieu lan khong tao lap cot, va case import truoc roi moi Encode payload.

## Verification
- `python -m py_compile gui/widgets/coding_value/coding_value_panel.py gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_check_button_adds_after_columns_and_compares_original_values`
- `python -m unittest tests.gui.test_coding_value_tab` (14 tests)
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts` (20 tests)

