# Coding Value stretch before decoded column

## Yeu cau
Neu phan table con khoang trong sau khi hien thi cac cot CHECK, tang kich thuoc cot `Decoded value (before)` de lap day phan con trong.

## Thay doi
- Cap nhat `_apply_column_widths()` de reset cac cot ve `Interactive` va set width co dinh nhu truoc.
- Khi cot 7 (`Decoded value (before)`) ton tai, set resize mode thanh `QHeaderView.Stretch` de cot nay an phan width con thua.
- Them regression test kiem tra cot 7 dung `Stretch` sau khi CHECK.

## Verification
- `python -m py_compile gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.gui.test_coding_value_tab` (16 tests)
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts` (22 tests)
