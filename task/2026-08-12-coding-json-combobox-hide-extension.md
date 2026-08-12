# Coding JSON combobox display name

## Yeu cau
Trong tab Coding Value, combobox `cmb_coding_json` khong hien thi duoi `.json`.

## Thay doi
- Doi display text cua tung file JSON tu `json_file.name` sang `json_file.stem`.
- Giu nguyen `currentData()` la duong dan file JSON day du de import/load van hoat dong nhu cu.
- Cap nhat tests de chon va verify ten hien thi khong co `.json`.

## Verification
- `python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_selecting_json_drop_list_loads_table_from_export_folder tests.gui.test_coding_value_tab.CodingValueTabTests.test_import_button_loads_selected_json_without_excel_warning tests.gui.test_coding_value_tab.CodingValueTabTests.test_import_coding_excel_refreshes_json_drop_list_and_loads_table_from_json`
- `python -m unittest tests.gui.test_coding_value_tab`
