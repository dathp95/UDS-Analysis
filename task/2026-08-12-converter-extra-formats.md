# Converter Extra Formats

Date: 2026-08-12

## Request
Bo sung them format cho converter trong tab CRC_Converter:
- Binary
- TXT
- Octa

## Implementation
- Mo rong `core/converter.py`:
  - Them `Binary`, `TXT`, `Octa` vao `SUPPORTED_FORMATS`.
  - `Binary`: parse theo tung byte 8 bit, chap nhan co hoac khong co khoang trang, output chuan hoa dang `01000001 01000010`.
  - `TXT`: dung UTF-8 de encode/decode text.
  - `Octa`: parse tung byte octal trong range `0..377`, output dang octal theo byte.
  - Giu `ASCII` rieng voi validate ASCII nhu cu.
- Cap nhat test core cho cac format moi va invalid cases.
- Cap nhat test UI de dam bao combobox hien thi format moi va convert duoc qua tab.

## Verification
- `python -m unittest tests.core.test_converter tests.gui.test_crc_converter_tab` passed: 16 tests.
- `python -m py_compile core/converter.py gui/tabs/crc_converter_tab.py tests/core/test_converter.py tests/gui/test_crc_converter_tab.py` passed.
- Offscreen `MainWindow` startup check passed: `MainWindow OK`.
