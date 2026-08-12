# Coding Value import exports JSON

## Yeu cau
Khi user bam nut Import trong tab Coding Value, tool van doc file Excel da chon va dong thoi export du lieu parse duoc ra JSON trong folder `export_coding_files` de tuong lai co the doc tu JSON thay vi Excel.

## Thay doi
- Them `EXPORT_CODING_FILES_DIR = PROJECT_ROOT / "export_coding_files"` vao `config.paths`.
- Them `export_coding_value_rows_to_json()` trong `core.coding_value` de serialize source file va rows/options da parse.
- Goi export JSON trong `CodingValuePanel.import_coding_value()` ngay sau khi doc Excel thanh cong.
- Them regression test dam bao Import tao file `export_coding_files/<ten_excel>.json` va noi dung row/options dung.

## Verification
- python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_import_coding_excel_exports_parsed_rows_to_json
- python -m py_compile config/paths.py core/coding_value.py gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py
- python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts
