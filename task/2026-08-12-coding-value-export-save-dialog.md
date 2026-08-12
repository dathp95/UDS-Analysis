# Coding Value export save dialog

## Yeu cau
Khi bam nut EXPORT trong tab Coding Value, mo hop thoai Save File de user co the sua ten file va bam Save.

## Thay doi
- Them Save File dialog cho `export_coding_value`.
- Giu default folder/name trong `Report_CodingValue/<date>` va ten `EEIV_report_Coding value_<datetime>.xlsx`.
- Neu user cancel thi khong export va khong hien success popup.
- Neu user nhap ten khong co `.xlsx`, tu dong them `.xlsx`.
- `_export_coding_report` ghi workbook vao duong dan user chon.
- Cap nhat tests export de mock `QFileDialog.getSaveFileName` va verify custom filename duoc dung.

## Verification
- `python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.gui.test_coding_value_tab`
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts`
