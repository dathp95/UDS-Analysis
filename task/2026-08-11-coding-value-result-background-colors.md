# Coding Value result background colors

## Yeu cau
Doi dinh dang cot Result tu mau chu sang mau nen:
- MATCH: background success/green.
- No-M: background warning/orange.

## Thay doi
- `_apply_result_style()` dat background theo `ThemeManager.fn_colors().SUCCESS/WARNING`.
- Dat foreground `TEXT_INVERT` de chu Result de doc tren nen mau.
- Test regression kiem tra background color cua MATCH va No-M.
- Refresh theme van apply lai style Result sau khi row background duoc refresh.

## Verification
- `python -m py_compile gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.gui.test_coding_value_tab` (16 tests)
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts` (22 tests)
