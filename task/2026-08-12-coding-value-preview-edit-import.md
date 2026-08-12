# Coding Value preview EDIT IMPORT

## Yeu cau
Doi nut preview Copy thanh EDIT. Sau khi user bam CHECK de tao ket qua so sanh, nut EDIT duoc bat. Bam EDIT cho phep sua chuoi data trong preview va doi nut thanh IMPORT. Bam IMPORT se nap chuoi do vao cot Raw value va Decoded Value (Editable).

## Thay doi
- Doi `btn_preview_copy` thanh `btn_preview_edit` voi label mac dinh `EDIT`.
- Them flow `EDIT -> IMPORT`: preview chuyen sang editable, sau do import payload moi vao table.
- Them `encode_payload(update_original=False)` de import payload sau CHECK khong reset gia tri before/original.
- Khi import preview sau CHECK, Raw value, Decoded Value (Editable), Result va working log duoc cap nhat; Raw value (before) va Decoded value (before) giu nguyen.
- Cap nhat test action state: preview EDIT chi active sau khi da CHECK.

## Verification
- python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_preview_edit_imports_payload_after_check_without_resetting_before
- python -m py_compile gui/widgets/coding_value/coding_value_panel.py gui/widgets/coding_value/coding_value_table.py tests/gui/test_coding_value_tab.py
- python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts
