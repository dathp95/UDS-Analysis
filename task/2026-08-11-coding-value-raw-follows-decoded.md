# Coding Value Raw Follows Decoded

## Request
- Cot Raw value phai hien thi gia tri raw tuong ung sau khi user chon Decoded Value.
- User chi sua/chon cot Decoded Value.
- Vi du `0x1=VF3`, `BitLength=8`: khi chon `VF3` thi Raw value hien `01`.

## Changes
- Gan raw value da format vao user data cua tung option trong decoded combobox.
- Khi combobox thay doi selection, table cap nhat cot Raw value cung row.
- Raw value cua option list duoc format khong co prefix `0x` va padding theo bit length.
- Bo sung UI test cho case chon `VF3` thi Raw value doi thanh `01`.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab`
- `python -m py_compile gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts`
- `python -m unittest discover` van loi do thieu dependency moi truong: `cryptography` va `can`.