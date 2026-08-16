# Coding Value Restore Clear Payload

## Request
Restore the `clear_coding_payload` button/function in Coding Value while keeping the removed table copy feature out.

## Changes
- Restored payload input `Clear` button after `Copy`.
- Reconnected `btn_clear` to `clear_coding_payload()`.
- Restored `clear_coding_payload()` to clear input payload and preview state without touching clipboard.
- Restored button state and theme refresh handling for `btn_clear`.
- Updated focused tests for layout, action state, and clear behavior.

## Verification
Passed:
- `python -m py_compile gui\widgets\coding_value\coding_value_panel.py tests\gui\test_coding_value_tab.py`
- Focused Coding Value tests for payload copy/clear, payload layout, action states, right-side action layout, and preview refresh/copy/edit.

Full `tests.gui.test_coding_value_tab` still has 2 unrelated width expectation failures: `cmb_coding_json` width and `filter_action_row` width.
