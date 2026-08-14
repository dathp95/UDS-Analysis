# Transfer CRC to Coding Value

Date: 2026-08-14

## Request
Them nut `Transfer CRC` trong tab CRC_Converter. Khi user tinh CRC va bam nut nay, CRC HEX se duoc transfer sang row CRC trong tab Coding Value va cap nhat Raw Value.

## Implementation
- Them `crc_transfer_requested = Signal(str)` trong `CRCConverterTab`.
- Them nut `Transfer CRC` canh `COPY CRC` trong CRC layout.
- Khi bam `Transfer CRC`:
  - Doc `txt_crc_output`.
  - Normalize HEX khong prefix, vi du `0x47` -> `47`.
  - Neu rong/invalid thi warning va khong emit.
  - Neu hop le thi emit `crc_transfer_requested.emit(crc_value)`.
- `MainWindow` chi connect signal:
  - `crc_converter_tab.crc_transfer_requested` -> `coding_value_tab.fn_set_crc_value`.
- Them public API `fn_set_crc_value` o `CodingValueTab` va `CodingValuePanel`.
- Them `CodingValueTable.fn_set_raw_value_by_parameter(...)` de search row theo ten parameter, khong hardcode row number.
- Raw Value update dung lai flow normalize/sync decoded/emit `raw_value_changed`, khong thao tac truc tiep tu MainWindow.

## Verification
- `python -m unittest tests.gui.test_crc_converter_tab.CRCConverterTabTests.test_transfer_crc_emits_normalized_crc_value tests.gui.test_crc_converter_tab.CRCConverterTabTests.test_transfer_crc_rejects_empty_output tests.gui.test_coding_value_tab.CodingValueTabTests.test_set_crc_value_updates_crc_parameter_row tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_crc_transfer_signal_updates_coding_value_tab` passed: 4 tests.
- `python -m unittest tests.gui.test_crc_converter_tab` passed: 16 tests.
- `python -m py_compile gui/tabs/crc_converter_tab.py gui/widgets/coding_value/coding_value_table.py gui/widgets/coding_value/coding_value_panel.py gui/tabs/coding_value_tab.py gui/windows/main_window.py tests/gui/test_crc_converter_tab.py tests/gui/test_coding_value_tab.py tests/gui/test_main_window_shortcuts.py` passed.
- Offscreen MainWindow startup check passed: `MainWindow OK`.

## Note
- Broad GUI test command hien co 2 failure khong thuoc feature nay:
  - `test_json_drop_list_starts_empty_between_browse_and_import`: expect width 200, UI hien la 300.
  - `test_license_support_tab_shows_support_and_contact_content`: expect old description text, UI hien la coffee text.