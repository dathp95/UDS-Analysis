# Coding Value table raw value copy

## Yeu cau
Nut COPY ben phai table trong tab Coding Value can copy gia tri cot Raw value, ghep thanh chuoi hex dang `xx xx xx`, hien thong bao copy thanh cong kem chuoi va popup tu tat sau 5 giay mac dinh. Thoi gian timeout co the truyen vao khi goi ham.

## Thay doi
- Connect `btn_table_copy` vao handler copy raw values.
- Them helper lay cot Raw value, bo gia tri rong, chuan hoa hex uppercase 2 ky tu va split token dai thanh tung byte.
- Copy chuoi vao clipboard va hien QMessageBox auto-close bang `QTimer.singleShot`.
- Them test cho copy raw values, timeout mac dinh 5000 ms va timeout tuy chinh cua popup.

## Verification
- python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_table_copy_button_copies_raw_values_and_shows_timed_message tests.gui.test_coding_value_tab.CodingValueTabTests.test_auto_close_information_uses_configurable_timeout
- python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py
- python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts
