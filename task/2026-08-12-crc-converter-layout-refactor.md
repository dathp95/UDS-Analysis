# CRC Converter layout refactor

## Yeu cau
Refactor tab `CRC_Converter` theo DRY/reusable component:
- Tach signal connect ra ham rieng.
- Chia layout thanh 2 nua: ben trai tinh CRC, ben phai danh cho Converter.
- Kiem tra scrollbar cho `txt_crc_input`.

## Thay doi
- Doi main layout cua `CRCConverterTab` sang `QHBoxLayout` voi `crc_panel` va `converter_panel` ti le 1:1.
- Tach `_connect_signals()` de connect `btn_calculate_crc.clicked`.
- Tach `_setup_crc_panel()` va `_setup_converter_panel()` de structure ro hon.
- Giu `txt_crc_input` la `QPlainTextEdit`, gioi han chieu cao 3 dong va ap dung scrollbar style chung bang `fn_apply_scrollbar_style`.
- Them label `Converter` o panel ben phai lam structure cho chuc nang converter sau nay.
- Cap nhat test GUI de verify layout 2 panel, input multiline, scrollbar style, va tinh CRC van dung.

## Verification
- `python -m py_compile core/crc.py gui/tabs/crc_converter_tab.py tests/gui/test_crc_converter_tab.py tests/gui/test_main_window_shortcuts.py`
- `python -m unittest tests.core.test_crc tests.gui.test_crc_converter_tab tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_coding_value_tab_is_next_to_log_analyzer tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_crc_converter_tab_is_available_with_crc_panel`
