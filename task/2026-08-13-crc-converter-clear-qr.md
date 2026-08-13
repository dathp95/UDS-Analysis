# CRC Converter Clear QR

Date: 2026-08-13

## Request
Them nut `Clear QR` trong tab CRC_Converter, nam cung hang voi `Create QR` va `Copy QR`, can le trai voi `txt_qr_input` va thang hang theo style nut `Calculate CRC`.

## Implementation
- Them `btn_clear_qr = PrimaryButton("Clear QR")` vao QR panel.
- Dat 3 nut `Create QR`, `Copy QR`, `Clear QR` trong cung `QHBoxLayout`, can trai va co stretch ben phai.
- Them signal trong `_connect_signals()` goi `clear_qr_code`.
- `clear_qr_code()` xoa `txt_qr_input`, xoa QR preview va disable `Copy QR`.
- Them refresh theme cho `btn_clear_qr`.
- Cap nhat GUI test cho button moi va behavior clear.

## Verification
- `python -m unittest tests.gui.test_crc_converter_tab` passed: 14 tests.
- `python -m py_compile gui/tabs/crc_converter_tab.py tests/gui/test_crc_converter_tab.py` passed.