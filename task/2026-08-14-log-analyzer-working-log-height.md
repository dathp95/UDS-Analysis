# Log Analyzer Working Log Height

## Request
Make the Log Analyzer working log use the remaining height under the `CLEAR TABLE` button.

## Changes
- Updated `RightPanel` so `ActionPanel` receives the full right-panel height.
- Removed the outer trailing stretch that was consuming the remaining space.
- Kept `txt_working_log` as the stretched widget inside `ActionPanel`.
- Added a focused test to guard the layout stretch behavior.

## Verification
- `python -m py_compile gui\widgets\log_analyzer\right_panel.py gui\widgets\log_analyzer\action_panel.py tests\gui\test_log_analyzer_working_log.py`
- `python -m unittest tests.gui.test_log_analyzer_working_log`
