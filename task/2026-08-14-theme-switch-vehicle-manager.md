# Move Theme Switch To Vehicle Manager

Date: 2026-08-14

## Request
Move `theme_switch` from Log Analyzer to the Vehicle Manager tab. Then refine the layout so `theme_switch` is in its own bottom layout on the right side, at the bottom-right corner.

## Changes
- Removed `ThemeSwitch` from `gui/widgets/log_analyzer/left_panel.py`.
- Removed Log Analyzer's theme-change signal handling because it no longer owns the switch.
- Added `ThemeSwitch` to `VehicleManagerTab`.
- Created a separate bottom `QHBoxLayout` in the right-side detail area of Vehicle Manager.
- Put only `theme_switch` in that bottom layout, with a left stretch so it stays at the bottom-right.
- Kept business action buttons, including `Save`, in the existing action row.
- Added `VehicleManagerTab.fn_change_theme()` to apply the selected theme and refresh the main window.
- Updated the `toggle_theme` shortcut target to use `vehicle_manager_tab.theme_switch`.
- Added a focused GUI test confirming the switch moved out of Log Analyzer and is the final widget in Vehicle Manager's separate bottom-right layout.

## Verification
- `python -m unittest tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_theme_switch_is_in_vehicle_manager_separate_bottom_right_layout tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_shortcuts_only_run_on_log_analyzer_tab` passed.
- `python -m py_compile gui\\tabs\\vehicle_manager_tab.py tests\\gui\\test_main_window_shortcuts.py` passed.
