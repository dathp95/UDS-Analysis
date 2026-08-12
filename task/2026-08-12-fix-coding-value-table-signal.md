# Fix CodingValueTable startup signal

## Loi
Chay `python main.py` bi loi:
`AttributeError: 'CodingValueTable' object has no attribute 'raw_value_changed'`.

## Nguyen nhan
`gui/widgets/coding_value/coding_value_table.py` bi mat nhieu phan code can thiet sau thao tac tick, trong do co:
- `raw_value_changed`
- `filter_by_parameter`
- cac cot CHECK/result
- logic bit-field payload
- style result va column width

## Thay doi
- Phuc hoi `gui/widgets/coding_value/coding_value_table.py` ve ban day du trong repo.
- Khong sua cac file khac ngoai scope.

## Verification
- `python -m py_compile gui/widgets/coding_value/coding_value_table.py gui/widgets/coding_value/coding_value_panel.py gui/tabs/coding_value_tab.py gui/windows/main_window.py main.py`
- `python -m unittest tests.gui.test_coding_value_tab`
- `python -m unittest tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_coding_value_tab_is_next_to_log_analyzer tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_crc_converter_tab_is_available_with_crc_panel`
- Khoi tao `MainWindow` offscreen voi mock `can/pandas`: `MainWindow OK`
