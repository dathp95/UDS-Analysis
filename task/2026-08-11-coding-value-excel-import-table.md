# Coding Value Excel Import Table

## Request
Thiet ke tab `Coding value` don gian giong Log Analyzer:
- User chon duong dan file Excel trong `config/Coding`.
- Mac dinh doc `config/Coding/MHU CDS Coding.xlsx`.
- Co nut `Import`.
- Doc parameter tu Excel, uu tien format hien tai `Parameter | BytePos | BitPos | BitLength | MethodType` va ho tro fallback header bat dau bang `$`.
- Render table `Parameter | Byte Pos | Bit Pos | Bit Lengh | Raw value | Decoded Value (Editable)`.
- Cot decoded value la combobox editable, options lay tu Excel.

## Change
- Added `core/coding_value.py`:
  - Doc workbook bang `openpyxl`.
  - Parse rows coding parameter tu sheet.
  - Parse options dang `0xVALUE=Label`.
  - Extract raw value tu payload theo BytePos/BitPos/BitLength.
- Added `gui/widgets/coding_value/coding_value_table.py`.
- Updated `gui/widgets/coding_value/coding_value_panel.py`:
  - File path input.
  - Browse button.
  - Import button.
  - Coding payload text area.
  - Result table with editable decoded combobox.
- Kept tab wiring from previous scaffold in `gui/tabs/coding_value_tab.py` and `gui/windows/main_window.py`.
- Added tests:
  - `tests/core/test_coding_value_excel.py`
  - `tests/gui/test_coding_value_tab.py`

## Verification
- Passed: `python -m unittest tests.core.test_coding_value_excel`
- Passed: `python -m unittest tests.gui.test_coding_value_tab`
- Passed: `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts`
- Passed: `python -m unittest tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts tests.gui.test_filter_box_payload_editing tests.gui.test_quick_access_export tests.gui.test_result_table_quick_filter`
- Passed: `python -m py_compile core/coding_value.py gui/tabs/coding_value_tab.py gui/widgets/coding_value/coding_value_panel.py gui/widgets/coding_value/coding_value_table.py tests/core/test_coding_value_excel.py tests/gui/test_coding_value_tab.py`
- Manual parser check with `config/Coding/MHU CDS Coding.xlsx` returned 53 rows and decoded sample values.
- Full `python -m unittest discover` still fails because local dependencies `cryptography` and `can` are missing.
