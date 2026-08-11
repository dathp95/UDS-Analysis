# Coding Value table column widths

## Yeu cau
Tinh chinh kich thuoc cot trong Coding Value table:
- Byte Pos, Bit Pos, Bit Length, Raw value nho lai.
- Decoded Value (Editable) rong bang Parameter.
- Decoded value (before) nho lai, chi lon hon Byte Pos mot chut.
- Noi dung bi cat can hien thi dau `...`.

## Thay doi
- Them `COLUMN_WIDTHS` trong `CodingValueTable` de quan ly width tap trung.
- Tat stretch last section de Result khong bi keo rong ngoai y muon.
- Apply width khi khoi tao table, khi import/set rows, va khi CHECK tao them cot before.
- Bat `Qt.ElideRight` cho table text va combobox dropdown/current width policy de noi dung dai hien thi dang rut gon.
- Them regression test cho width/ellipsis.

## Verification
- `python -m py_compile gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.gui.test_coding_value_tab` (16 tests)
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts` (22 tests)
