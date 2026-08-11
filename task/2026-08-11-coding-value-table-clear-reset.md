# Coding Value table CLEAR reset

## Yeu cau
Nut CLEAR ben phai table trong tab Coding Value can dua cac cot Raw value, Decoded Value editable, Raw value before, Decoded value before, Result va working log ve rong.

## Thay doi
- Connect btn_table_clear voi clear_table_coding_values().
- Them CodingValueTable.clear_coding_values() de reset raw, decoded combo, before/result columns, selection va state baseline raw.
- clear_table_coding_values() clear working log va preview/baseline payload de disable CHECK/table actions.
- Them regression test click nut CLEAR that.

## Verification
- python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_table_clear_button_resets_coding_values_and_working_log
- python -m py_compile gui/widgets/coding_value/coding_value_panel.py gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py
- python -m unittest tests.gui.test_coding_value_tab
- python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts