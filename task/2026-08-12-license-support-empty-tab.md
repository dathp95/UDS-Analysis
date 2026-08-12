# License & Support empty tab

## Yeu cau
Tao tab rong nam ben phai tab Vehicle Manager voi ten `License & Support`.

## Thay doi
- Tao `gui/tabs/license_support_tab.py` voi class `LicenseSupportTab` va base `QVBoxLayout` rong.
- Them `license_support_tab` vao `MainWindow` sau `vehicle_manager_tab`.
- Them tab text `License & Support` o ben phai `Vehicle Manager`.
- Sua loi startup do `coding_value_panel.py` import `REPORT_DIR` khong con ton tai; chuyen sang `CODING_VALUE_REPORT_DIR`.
- Sua loi cu phap test bi chen literal `` `r`n `` do turn truoc bi interrupt.

## Verification
- `python -m py_compile main.py gui/windows/main_window.py gui/tabs/license_support_tab.py gui/widgets/coding_value/coding_value_panel.py tests/gui/test_main_window_shortcuts.py`
- `python -m unittest tests.gui.test_main_window_shortcuts`
