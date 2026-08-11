# Coding Value CHECK clear selection

## Yeu cau
Sau khi user bam CHECK, table Coding Value can clear selected row/cell va bo current cursor khoi table.

## Thay doi
- Them clearSelection() va setCurrentCell(-1, -1) sau khi apply check results.
- Them regression test cho workflow select row truoc CHECK va clear selection sau CHECK.

## Verification
- python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_check_button_clears_table_selection
- python -m unittest tests.gui.test_coding_value_tab
- python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts
- python -m py_compile gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py