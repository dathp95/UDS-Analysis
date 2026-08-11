# Coding Value MethodType colon separator

## Yeu cau
Noi dung cot $MethodType co the dung dau '=' hoac ':' giua raw value va decoded label. Vi du 0x2: De Sat Silver phai decode duoc thanh De Sat Silver.

## Thay doi
- Mo rong _OPTION_PATTERN trong core/coding_value.py de chap nhan ca '=' va ':'.
- Them regression test voi $MethodType dang nhieu dong su dung dau ':'.

## Verification
- python -m unittest tests.core.test_coding_value_excel.CodingValueExcelTests.test_method_type_accepts_colon_separator
- python -m py_compile core/coding_value.py tests/core/test_coding_value_excel.py gui/widgets/coding_value/coding_value_panel.py gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py
- python -m unittest tests.core.test_coding_value_excel
- python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts