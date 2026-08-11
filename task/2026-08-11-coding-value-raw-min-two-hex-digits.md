# Coding Value Raw Minimum Two Hex Digits

## Request
- Khi user nhap Raw value o byte 39 nhu `03`, UI phai giu `03`, khong rut gon thanh `3`.
- Neu user nhap `1` thi render `01`; nhap `D` thi render `0D`.

## Root Cause
- Formatter Raw value dang tinh width theo `BitLength`.
- Voi `BitLength=4`, width bi tinh thanh 1 nibble, nen `03` thanh `3`.

## Changes
- Doi formatter de Raw value luon hien thi toi thieu 2 ky tu hex.
- Van giu validate theo gia tri so cua `BitLength`: vi du `BitLength=4`, `D` hop le nhung `10` khong hop le.
- Bo sung regression test cho `03`, `1`, `D`, va overflow `10`.

## Verification
- `python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_raw_value_keeps_two_hex_digits_for_nibble_values`
- `python -m py_compile gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.gui.test_coding_value_tab`
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts`
- `python -m unittest discover` van fail do thieu dependency moi truong: `cryptography` va `can`.