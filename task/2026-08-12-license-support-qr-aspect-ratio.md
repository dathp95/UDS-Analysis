# License & Support QR aspect ratio

## Yeu cau
Sua anh QR trong tab `License & Support` de khong bi bop meo va giu nguyen ti le kich thuoc.

## Thay doi
- Tat `setScaledContents(True)` tren `qr_label`.
- Luu pixmap goc vao `support_qr_pixmap`.
- Scale pixmap hien thi bang `Qt.KeepAspectRatio` va `Qt.SmoothTransformation`.
- Khoi phuc title `Support the development ☕`.
- Cap nhat test de verify label khong dung scaled contents va ti le pixmap hien thi khop pixmap goc.

## Verification
- `python -m unittest tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_license_support_tab_shows_support_and_contact_content`
- `python -m unittest tests.gui.test_main_window_shortcuts`
- `python -m py_compile gui/tabs/license_support_tab.py tests/gui/test_main_window_shortcuts.py`
