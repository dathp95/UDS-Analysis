# CRC Converter Button States

Date: 2026-08-13

## Request
Kiem tra va thiet lap trang thai nut trong tab Converter/CRC_Converter. Ban dau cac nut can deactive: `CLEAR`, `Copy Result`, `Clear QR`.

## Implementation
- Giu nguyen layout QR user vua chinh.
- `btn_converter_clear` disable ban dau, active khi Converter co input hoac output.
- `btn_converter_copy` disable ban dau, active khi Converter co output.
- `btn_clear_qr` disable ban dau, active khi QR input co text hoac QR preview da duoc tao.
- `btn_copy_qr` van active chi khi co QR preview.
- Them updater rieng:
  - `_update_converter_button_states()`
  - `_update_qr_button_states()`
- Noi `textChanged` cua Converter input/output va QR input de cap nhat button state.
- Cap nhat tests cho initial state va state sau convert/clear/invalid input/QR clear.

## Verification
- `python -m unittest tests.gui.test_crc_converter_tab` passed: 14 tests.
- `python -m py_compile gui/tabs/crc_converter_tab.py tests/gui/test_crc_converter_tab.py` passed.
- `python -m py_compile main.py gui/tabs/crc_converter_tab.py tests/gui/test_crc_converter_tab.py` passed.