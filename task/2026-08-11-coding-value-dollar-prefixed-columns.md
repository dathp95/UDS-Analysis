# Coding Value dollar-prefixed Excel columns

## Yeu cau
Khi file sheet Excel co nhieu cot, Coding Value import can tap trung lay bo cot co tien to $ nhu $Parameter, $BytePos (from 0), $BitPos, $BitLength, $MethodType.

## Thay doi
- Them regression test voi ca cot $ va cot thuong, trong do cot thuong nam sau de chac chan khong override cot $.
- Them _parameter_table_headers() de neu header row co du bo cot bat buoc dang $ thi chi map cac cot $.
- Them _has_required_dollar_headers() de giu fallback format cu khi file chua co du bo cot $.

## Verification
- python -m unittest tests.core.test_coding_value_excel.CodingValueExcelTests.test_prefers_dollar_prefixed_parameter_table_columns
- python -m py_compile core/coding_value.py tests/core/test_coding_value_excel.py gui/widgets/coding_value/coding_value_panel.py gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py
- python -m unittest tests.core.test_coding_value_excel
- python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts