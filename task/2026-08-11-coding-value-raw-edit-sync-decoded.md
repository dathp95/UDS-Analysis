# Coding Value Raw Edit Sync Decoded

## Request
- User co the sua cot Raw value.
- Decoded Value phai hien thi gia tri tuong ung voi Raw value moi.
- Raw value chi hop le trong do dai `BitLength`.
- Tool tu format raw thanh dang `XX XX XX` khi `BitLength > 4`.
- Neu raw user nhap vuot qua `BitLength`, hien popup bao byte do khong hop le.

## Changes
- Cho phep edit rieng cot Raw value trong Coding value table.
- Luu metadata theo row: `BitLength`, byte position, raw hop le gan nhat.
- Khi Decoded Value thay doi, Raw value tiep tuc cap nhat theo option da chon.
- Khi Raw value thay doi, tool validate hex, gioi han theo `BitLength`, format lai raw, va sync combobox decoded.
- Neu raw vuot gioi han, tool revert ve raw hop le gan nhat va goi `QMessageBox.warning`.
- Bo sung test cho raw editable, sync decoded, format `01 23`, va overflow warning.

## Verification
- `python -m py_compile gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.gui.test_coding_value_tab`
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts`
- `python -m unittest discover` van fail do thieu dependency moi truong: `cryptography` va `can`.