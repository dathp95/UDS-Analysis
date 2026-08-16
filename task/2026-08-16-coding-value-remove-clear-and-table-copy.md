# Coding Value Remove Unused Clear And Table Copy

## Request
Clean up unused `clear_coding_payload` behavior and remove `btn_table_copy` from Coding Value.

## Changes
- Removed payload input `Clear` button and `clear_coding_payload()` slot.
- Removed table-side `COPY` button (`btn_table_copy`) and its signal/state/theme wiring.
- Removed table raw-value copy helpers and the auto-close info helper that were only used by the removed table copy flow.
- Updated tests for the new payload input layout and table action layout.

## Verification
Passed:
- `python -m py_compile gui\widgets\coding_value\coding_value_panel.py tests\gui\test_coding_value_tab.py`
- Focused Coding Value tests for payload copy, payload layout, action states, table-side action layout, preview refresh/copy/edit, and table clear behavior.
- `rg` check confirmed no stale references to removed clear/table-copy symbols.

Full `tests.gui.test_coding_value_tab` still has 2 unrelated width expectation failures: `cmb_coding_json` width and `filter_action_row` width.
