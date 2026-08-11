# Coding Value CLEAR whole table

## Yeu cau
Nut CLEAR ben phai table trong tab Coding Value can clear ca table, khong chi clear cac gia tri trong row.

## Thay doi
- Doi handler clear_table_coding_values() de goi CodingValueTable.clear_rows().
- Bo helper clear_coding_values() va import QBrush khong con dung.
- Cap nhat regression test de kiem tra sau khi click CLEAR thi rowCount = 0, working log va preview rong, action buttons deactivate.

## Verification
- python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_table_clear_button_clears_table_and_working_log
- python -m py_compile gui/widgets/coding_value/coding_value_panel.py gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py
- python -m unittest tests.gui.test_coding_value_tab
- python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts