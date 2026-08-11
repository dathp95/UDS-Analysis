# Coding Value CHECK fixed before columns

## Yeu cau
Doi 3 cot tao khi bam CHECK thanh:
- Raw value (before)
- Decoded value (before)
- Result

Hai cot before phai la snapshot co dinh theo gia tri luc Encode/import payload, khong thay doi khi user sua Raw value hoac Decoded Value (Editable). Khi user thay doi gia tri editable, chi Result cap nhat MATCH/No-M dua tren raw hien tai so voi raw before.

## Thay doi
- Doi header CHECK tu after sang before.
- `apply_check_results()` ghi snapshot before vao cot 6/7 va tinh Result theo raw hien tai.
- Khi user sua decoded combobox/raw value, chi cap nhat cot Result, khong ghi de cot before.
- Cap nhat regression tests cho ten cot before va behavior before fixed.

## Verification
- `python -m py_compile gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.gui.test_coding_value_tab` (15 tests)
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts` (21 tests)
