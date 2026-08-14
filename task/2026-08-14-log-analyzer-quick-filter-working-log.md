# Log Analyzer Quick Filter Working Log

## Request
Add a working log display under the Log Analyzer `CLEAR TABLE` button. When the user selects a quick filter, the log should show the selected filter details and replace the previous filter details.

## Changes
- Added a read-only `txt_working_log` editor below `CLEAR TABLE` in `ActionPanel`.
- Added `fn_set_quick_filter_log()` to format and display `Name`, `ECU`, `Request`, and `Response`.
- Added `fn_clear_working_log()` and clear it when `CLEAR TABLE` is triggered.
- Connected `LogAnalyzerTab.fn_quick_filter()` to update the working log before applying the table filter.
- Added focused GUI tests for quick filter working-log display/replacement and clear behavior.

## Verification
- `python -m py_compile gui\widgets\log_analyzer\action_panel.py gui\tabs\log_analyzer_tab.py tests\gui\test_log_analyzer_working_log.py`
- `python -m unittest tests.gui.test_log_analyzer_working_log`
- `python -m unittest tests.gui.test_result_table_quick_filter`
