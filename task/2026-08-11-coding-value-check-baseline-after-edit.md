# Coding Value CHECK baseline before editable changes

## Yeu cau
Sau khi user bam CHECK, 3 cot after moi tao phai hien thi gia tri before/baseline, giu nguyen nhu luc Encode payload. Sau do, khi user thay doi gia tri trong cot Decoded Value (Editable) hoac Raw value, cac cot after moi cap nhat theo gia tri vua sua va Result chuyen MATCH/No-M tuong ung.

## Thay doi
- `apply_check_results()` khoi tao cot after bang `original_raw` thay vi raw hien tai.
- Them helper cap nhat ket qua after khi cot check da hien thi.
- Goi cap nhat after/result sau khi user doi combobox decoded value hoac sua raw value.
- Cap nhat regression tests cho workflow CHECK truoc, edit sau.

## Verification
- `python -m py_compile gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.gui.test_coding_value_tab` (15 tests)
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts` (21 tests)
