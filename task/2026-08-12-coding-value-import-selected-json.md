# Coding Value Import selected JSON

## Yeu cau
Khi user chon file trong `cmb_coding_json` roi bam `btn_import`, khong hien popup warning yeu cau chon Excel file.

## Thay doi
- Them regression test cho case `cmb_coding_json` da chon file JSON, `file_path` Excel rong, bam Import khong goi `QMessageBox.warning`.
- Cap nhat `import_coding_value()` de uu tien load selected JSON khi co selection va Excel path rong.
- Giu nguyen flow Import Excel: neu co Excel path thi van parse Excel, export JSON, va load table tu JSON vua export.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_import_button_loads_selected_json_without_excel_warning`
- `python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.gui.test_coding_value_tab`
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts`