# Log Analyzer Width Ratio

Date: 2026-08-14

## Request
Adjust the Log Analyzer display width so the result table area is prioritized, while the left panel is slightly smaller.

## Changes
- Exposed `LogAnalyzerTab.content_layout` for layout verification.
- Changed content stretch ratio from `left/table/right = 3/7/2` to `2/9/2`.
- This makes the left quick-filter panel narrower and gives more horizontal space to the result table while keeping the right action panel usable.
- Added a focused GUI test for the new stretch ratio.

## Verification
- `python -m unittest tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_log_analyzer_prioritizes_result_table_width tests.gui.test_quick_access_export` passed.
- `python -m py_compile gui\\tabs\\log_analyzer_tab.py tests\\gui\\test_main_window_shortcuts.py` passed.
