# Coding Value empty initial file path

## Yeu cau
File path trong tab Coding Value can de rong ban dau, khong tu dien file Excel mac dinh.

## Thay doi
- Bo viec set text mac dinh `config/Coding/MHU CDS Coding.xlsx` cho `file_path` khi khoi tao `CodingValuePanel`.
- Giu `DEFAULT_CODING_DIR` de nut Browse van mo san folder `config/Coding`.
- Xoa constant `DEFAULT_CODING_FILE` vi khong con su dung.
- Them regression test dam bao `file_path` rong khi panel moi duoc tao.

## Verification
- python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_file_path_starts_empty
- python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py
- python -m unittest tests.gui.test_coding_value_tab
- python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts
