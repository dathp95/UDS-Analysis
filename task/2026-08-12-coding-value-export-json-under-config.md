# Coding Value export JSON under config

## Yeu cau
Chuyen folder `export_coding_files` vao ben trong folder `config`.

## Thay doi
- Chuyen `EXPORT_CODING_FILES_DIR` sang `CONFIG_DIR / "export_coding_files"`.
- Cap nhat test de khoa behavior export JSON tai `config/export_coding_files`.
- Move thu muc thuc te `export_coding_files` hien co vao `config/export_coding_files` va giu lai file JSON ben trong.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_export_coding_files_dir_lives_under_config tests.gui.test_coding_value_tab.CodingValueTabTests.test_import_coding_excel_exports_parsed_rows_to_json`
- `python -m py_compile config/paths.py core/coding_value.py gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts`