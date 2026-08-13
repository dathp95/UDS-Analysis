# CRC Converter QR Code Generator

Date: 2026-08-13

## Request
Them chuc nang tao ma QR code, nam duoi layout Converter trong tab CRC_Converter.

## Implementation
- Them `core/qr_generator.py` voi API `generate_qr_png_bytes(text: str) -> bytes`.
- Reject empty input va tao QR PNG bytes trong memory, khong ghi temp file.
- Them dependency `qrcode[pil]==8.2` vao `requirements.txt`.
- Cap nhat `gui/tabs/crc_converter_tab.py`:
  - Them section `QR Code Generator` duoi Converter.
  - Them multiline input editor, `Create QR`, `Copy QR`.
  - Them `QLabel` preview fixed 180x180, canh giua, scale keep aspect ratio.
  - Copy QR image vao clipboard bang pixmap.
  - Signal connection nam trong `_connect_signals()`.
  - QR generation logic khong nam trong GUI.
- Cap nhat tests cho core QR va GUI tab CRC_Converter.

## Verification
- Cai dependency runtime: `python -m pip install "qrcode[pil]==8.2"` passed.
- Cai dependency runtime co san trong requirements de test app: `python -m pip install python-can==4.6.1` passed.
- Real QR generation check passed: PNG header `b'\x89PNG\r\n\x1a\n'`.
- `python -m unittest tests.core.test_qr_generator tests.gui.test_crc_converter_tab` passed: 16 tests.
- `python -m py_compile core/qr_generator.py gui/tabs/crc_converter_tab.py tests/core/test_qr_generator.py tests/gui/test_crc_converter_tab.py` passed.
- Offscreen MainWindow startup check passed: `MainWindow OK`.