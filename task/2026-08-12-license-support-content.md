# License & Support content

## Yeu cau
Hien thi noi dung support, QR image va contact trong tab `License & Support`.

## Thay doi
- Them title `Support the development ☕`.
- Them description support continued development.
- Hien thi QR image tu `gui/resources/images/support.qr.jpg` neu co, fallback sang file hien co `support_qr.jpg`.
- Them contact email va phone, cho phep select text.
- Cap nhat test main window de verify noi dung va QR pixmap render duoc.

## Verification
- `python -m unittest tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_license_support_tab_shows_support_and_contact_content`
- `python -m py_compile gui/tabs/license_support_tab.py gui/windows/main_window.py tests/gui/test_main_window_shortcuts.py`
- `python -m unittest tests.gui.test_main_window_shortcuts`
