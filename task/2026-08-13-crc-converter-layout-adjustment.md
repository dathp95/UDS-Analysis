# CRC Converter Layout Adjustment

Date: 2026-08-13

## Request
Dieu chinh layout phan Converter trong tab CRC_Converter:
- O Input cung hang voi Output.
- Nut `Copy Result` cung hang voi 3 nut `CONVERT`, `SWAP`, `CLEAR`.

## Implementation
- Cap nhat `_setup_converter_panel()` trong `gui/tabs/crc_converter_tab.py`.
- Tao `editor_layout` dang `QHBoxLayout` gom 2 cot:
  - Input label + editor
  - Output label + editor
- Chuyen `btn_converter_copy` vao chung `action_layout` sau nut `CLEAR`.
- Khong thay doi logic convert/copy/swap/clear.

## Verification
- `python -m unittest tests.gui.test_crc_converter_tab` passed: 10 tests.
- `python -m py_compile gui/tabs/crc_converter_tab.py tests/gui/test_crc_converter_tab.py` passed.
