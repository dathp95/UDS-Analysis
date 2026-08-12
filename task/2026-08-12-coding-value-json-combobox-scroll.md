# Coding Value JSON combobox scroll

## Yeu cau
Chinh `cmb_coding_json` hien thi toi da 5 gia tri; neu nhieu hon thi co scrollbar theo style hien co.

## Thay doi
- Set `cmb_coding_json.setMaxVisibleItems(5)`.
- Apply scrollbar style cho popup view cua `cmb_coding_json`.
- Bo sung test dam bao dropdown JSON co width 200, max visible 5 va scrollbar style.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_json_drop_list_starts_empty_between_browse_and_import`
- `python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.gui.test_coding_value_tab`
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts`