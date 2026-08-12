# Coding Value JSON dropdown

## Yeu cau
Them drop-list giua nut Browse va Import, width 200, lay file tu `config/export_coding_files`. Khi Import Excel, file JSON vua export hien thi trong drop-list va table render du lieu tu JSON.

## Thay doi
- Them `load_coding_value_rows_from_json` de doc lai rows/options tu file JSON export.
- Them `cmb_coding_json` vao file row cua tab Coding Value, nam giua `btn_browse` va `btn_import`, width 200, startup khong chon item.
- Refresh danh sach JSON tu `config/export_coding_files` va cho phep chon JSON co san de render table.
- Flow Import Excel bay gio export JSON truoc, chon file JSON vua tao trong drop-list, roi load table tu JSON.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_json_drop_list_starts_empty_between_browse_and_import tests.gui.test_coding_value_tab.CodingValueTabTests.test_import_coding_excel_refreshes_json_drop_list_and_loads_table_from_json`
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_selecting_json_drop_list_loads_table_from_export_folder tests.gui.test_coding_value_tab.CodingValueTabTests.test_import_coding_excel_refreshes_json_drop_list_and_loads_table_from_json`
- `python -m unittest tests.gui.test_coding_value_tab`
- `python -m py_compile config/paths.py core/coding_value.py gui/widgets/coding_value/coding_value_panel.py gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts`