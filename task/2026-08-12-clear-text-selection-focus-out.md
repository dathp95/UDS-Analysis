# Clear Text Selection On Focus Out

Date: 2026-08-12

## Request
Kiem tra va sua tab Coding value va CRC_Converter vi cac LineEdit/text editor co the giu nhieu vung boi chon cung luc, tao hanh vi khong mong muon.

## Root Cause
`QPlainTextEdit` giu cursor selection sau khi widget mat focus, nen khi user chuyen sang field khac co the thay nhieu vung text van dang duoc boi chon. `QLineEdit` thuong tu clear selection khi focus out, nhung van duoc dua vao helper de hanh vi thong nhat.

## Implementation
- Them `gui/utils/text_selection.py` voi helper `clear_text_selection_on_focus_out(parent, widgets)`.
- Helper clear selection khi `FocusOut` cho:
  - `QLineEdit`
  - `QPlainTextEdit`
  - `QTextEdit`
- Ap dung helper cho cac text widgets trong:
  - `CRCConverterTab`
  - `CodingValuePanel`
- Giu nguyen kha nang user boi chon/copy/sua khi widget dang focus.

## Verification
- Them regression tests cho CRC_Converter va Coding value.
- `python -m unittest tests.gui.test_crc_converter_tab.CRCConverterTabTests.test_text_selection_is_cleared_when_crc_editor_loses_focus tests.gui.test_crc_converter_tab.CRCConverterTabTests.test_text_selection_is_cleared_when_crc_lineedit_loses_focus tests.gui.test_coding_value_tab.CodingValueTabTests.test_text_selection_is_cleared_when_coding_lineedit_loses_focus tests.gui.test_coding_value_tab.CodingValueTabTests.test_text_selection_is_cleared_when_coding_editor_loses_focus` passed.
- `python -m unittest tests.gui.test_crc_converter_tab tests.gui.test_coding_value_tab` passed: 45 tests.
- `python -m py_compile gui/utils/text_selection.py gui/tabs/crc_converter_tab.py gui/widgets/coding_value/coding_value_panel.py tests/gui/test_crc_converter_tab.py tests/gui/test_coding_value_tab.py` passed.
- Offscreen MainWindow startup check passed: `MainWindow OK`.
