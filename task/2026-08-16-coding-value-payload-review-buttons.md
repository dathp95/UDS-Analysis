# Coding Value Payload Review Buttons

## Request
Review `coding_value_panel.py` after changing the payload review actions to `Refresh - Copy - Edit/Import`.

## Findings And Fixes
- Replaced stale `btn_preview_clear` references with `btn_copy_preview`.
- Added `copy_coding_preview()` so the preview Copy button has a valid slot.
- Updated payload review layout tests to assert `Refresh - Copy - EDIT/IMPORT - Preview`.
- Fixed `clear_coding_payload()` so Clear clears the input/preview instead of copying preview text to the clipboard.

## Verification
Passed:
- `python -m py_compile gui\widgets\coding_value\coding_value_panel.py tests\gui\test_coding_value_tab.py`
- Focused unittest cases for payload layout, action states, clear behavior, preview copy, and edit/import.

Full `tests.gui.test_coding_value_tab` still has 3 unrelated expectation failures around existing widths and copy-table message/timeout.
