# CRC Converter Copy Result Alignment

Date: 2026-08-13

## Request
Can chinh nut `Copy Result` thang voi le trai cua o `Output` trong phan Converter cua tab CRC_Converter.

## Implementation
- Giu Input/Output cung mot hang, chia 2 cot bang nhau.
- Chia hang action thanh 2 layout con cung stretch:
  - Cot trai: `CONVERT`, `SWAP`, `CLEAR`.
  - Cot phai: `Copy Result`, canh trai theo cot `Output`.
- Khong thay doi logic convert/swap/clear/copy.

## Verification
- `python -m unittest tests.gui.test_crc_converter_tab` passed: 10 tests.
- `python -m py_compile gui/tabs/crc_converter_tab.py tests/gui/test_crc_converter_tab.py` passed.
