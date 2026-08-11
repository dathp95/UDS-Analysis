# Coding Value export No-M warning fill

## Yeu cau
Khi export Excel tu tab Coding Value, nhung row co Result = No-M can duoc to mau warning.

## Thay doi
- Them PatternFill va ThemeManager vao CodingValuePanel de su dung mau WARNING cua theme hien tai.
- Khi export, lay index cot Result theo header va to fill ca row Excel neu Result = No-M.
- Them regression test mo workbook export de kiem tra row No-M co fill solid mau warning.

## Verification
- python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_export_button_highlights_no_match_rows_with_warning_fill
- python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py
- python -m unittest tests.gui.test_coding_value_tab
- python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts
