# Coding Value BitLength Text Validation

## Request
- Kiem tra vi sao `BitLength=4`, byte 39 van cho user nhap Raw value `08 09`.

## Root Cause
- Validator Raw value chi validate khi parse duoc `BitLength` thanh so.
- Neu gia tri BitLength tu Excel/UI la text nhu `4.0` hoac `4 bit`, `_to_int()` tra ve `None`.
- Khi `BitLength=None`, validator bo qua gioi han bit length, nen `08 09` duoc chap nhan.

## Changes
- Cap nhat `_to_int()` trong `gui/widgets/coding_value/coding_value_table.py` de parse duoc `4`, `4.0`, va `4 bit` thanh `4`.
- Cap nhat `_to_int()` trong `core/coding_value.py` de core parser cung xu ly BitLength text nhat quan.
- Bo sung UI regression test: `BitLength="4.0"` va `"4 bit"` phai reject `08 09`, nhung `08` van hop le.
- Bo sung core regression test: `BitLength="4.0"` van extract/decode bit field dung.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_raw_value_rejects_multiple_bytes_when_bit_length_is_nibble_text`
- `python -m unittest tests.core.test_coding_value_excel.CodingValueExcelTests.test_bit_length_text_is_parsed_for_bit_field_decode`
- `python -m py_compile core/coding_value.py gui/widgets/coding_value/coding_value_table.py tests/core/test_coding_value_excel.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts`
- Direct check: `4`, `4.0`, `4 bit` deu reject `08 09`.
- `python -m unittest discover` van fail do thieu dependency moi truong: `cryptography` va `can`.