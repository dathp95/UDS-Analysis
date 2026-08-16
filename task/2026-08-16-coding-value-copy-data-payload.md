# Coding Value Copy Data Payload Button

## Request
Add a `COPY DATA PAYLOAD` button under `CHECK` in Coding Value. The button copies the value from `txt_coding_preview` starting at byte 3.

## Changes
- Added `btn_copy_data_payload` under `btn_check` in the right-side action panel.
- Added `copy_data_payload()` to parse preview bytes, skip the first 3 bytes, and copy the remaining bytes as `XX XX`.
- Added button state/theme/signal wiring.
- Added focused tests for layout, enabled state, and clipboard output.

## Verification
Passed:
- `python -m py_compile gui\widgets\coding_value\coding_value_panel.py tests\gui\test_coding_value_tab.py`
- Focused Coding Value tests for action states, copy data payload, side action layout, and payload clear behavior.

Full `tests.gui.test_coding_value_tab` still has 2 unrelated width expectation failures: `cmb_coding_json` width and `filter_action_row` width.
