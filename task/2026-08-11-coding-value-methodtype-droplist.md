# Coding Value MethodType Droplist

## Request
- Doi thuoc tinh `$MethodType` thanh droplist.
- Popup chi hien thi toi da 5 gia tri.
- Neu nhieu hon 5 gia tri thi dung scrollbar theo style hien co cua project.

## Changes
- Cell decoded value co `decoded_options` tu Excel duoc chuyen thanh droplist non-editable.
- Gioi han popup combobox cho option list con 5 item bang `setMaxVisibleItems(5)`.
- Ap dung scrollbar style hien co cho popup view cua combobox bang `fn_apply_scrollbar_style(combo.view())`.
- Bo sung UI test de dam bao option list khong editable, max visible items la 5 va scrollbar style duoc gan.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab`
- `python -m unittest tests.core.test_coding_value_excel`
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts`
- `python -m py_compile gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py`