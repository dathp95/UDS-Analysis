# Coding Value result status colors

## Yeu cau
Dinh dang cot Result trong Coding Value table:
- MATCH hien thi mau success/green.
- No-M hien thi mau warning/orange.

## Thay doi
- Dung `ThemeManager.fn_colors().SUCCESS` va `WARNING` de lay mau theo theme hien tai.
- Them `_apply_result_style()` trong `CodingValueTable` va goi moi khi cap nhat Result.
- Re-apply mau Result khi refresh theme de doi light/dark van dung token.
- Bo sung regression test kiem tra foreground cua MATCH/No-M.

## Verification
- `python -m py_compile gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.gui.test_coding_value_tab` (16 tests)
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts` (22 tests)
