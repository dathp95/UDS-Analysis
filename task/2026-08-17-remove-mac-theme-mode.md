# Remove MAC Theme Mode

## Request
Remove the MAC theme mode/toggle and return the Vehicle Manager theme controls to the previous normal theme-switch behavior and position.

## Changes
- Removed MACOS theme enum/color/ThemeManager changes.
- Removed the MAC label, MAC toggle, MAC signal handler, and MAC priority/restore logic from Vehicle Manager.
- Restored Vehicle Manager bottom theme layout to the old order: theme switch first, stretch after it.
- Updated the theme-switch layout test to match the restored position.

## Verification
- `rg -n "MACOS|toggle_mac|lbl_mac|_on_mac_theme_toggled|_previous_normal_theme|MACOS_COLORS|test_mac_theme" gui tests` returned no matches.
- `python -m py_compile gui\tabs\vehicle_manager_tab.py tests\gui\test_main_window_shortcuts.py`
- `python -m unittest tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_theme_switch_is_in_vehicle_manager_separate_bottom_layout`