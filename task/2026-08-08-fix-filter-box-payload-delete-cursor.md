# Fix Filter Box Payload Delete Cursor

## Request
Khi user search payload trong filter box, vi du `22 F1 90`, roi sua thanh `22 F3 90`, thao tac dat cursor sau `3` va bam Delete khong duoc xoa sai ky tu `9`.

## Root Cause
Filter box format lai payload trong `textEdited` bang cach set text moi va dat cursor theo `cursor + 1`. Khi formatter tu chen/xoa khoang trang, cursor cu khong con map dung voi vi tri hex user dang sua.

## Change
- Them helper trong `gui/utils/payload_format.py` de format payload kem cursor theo so ky tu payload truoc cursor.
- Them helper Delete de bo qua khoang trang tu format va xoa ky tu hex ke tiep.
- Cap nhat `gui/widgets/log_analyzer/filter_box.py` dung helper moi.
- Cap nhat `gui/dialogs/quick_filter_dialog.py` cho Request/Response fields de tranh lap lai loi cursor.
- Them regression tests cho formatter va FilterBox.

## Verification
- Passed: `python -m unittest tests.core.test_payload_format`
- Passed: `python -m unittest tests.gui.test_filter_box_payload_editing`
- Passed: `python -m unittest tests.core.test_payload_format tests.gui.test_filter_box_payload_editing tests.gui.test_quick_access_export`
- Passed: `python -m py_compile gui/utils/payload_format.py gui/widgets/log_analyzer/filter_box.py gui/dialogs/quick_filter_dialog.py tests/core/test_payload_format.py tests/gui/test_filter_box_payload_editing.py`
- Full `python -m unittest discover` still fails because local dependencies `cryptography` and `can` are missing.
