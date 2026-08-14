# License Feature Access

Date: 2026-08-14

## Request
Change startup/license behavior so the application always opens. A valid license enables all tabs; missing, invalid, or expired license enables only CRC_Converter and License & Support.

## Changes
- Added `core/feature_access.py` with centralized `Feature` enum and feature access policy.
- Added `LicenseStatus` and `LicenseManager.get_status()` so license validation returns status without blocking startup.
- Updated `main.py` to always create `MainWindow` and show `Limited Mode` in the title when no valid license is available.
- Updated `MainWindow` to associate tabs with feature identifiers and apply access via the central policy.
- When license is invalid, MainWindow selects the first enabled tab, currently `CRC_Converter`.
- Updated README files to describe Limited Mode.
- Added focused tests for feature access policy, license status, startup behavior, and tab access.

## Verification
- `python -m unittest tests.core.test_feature_access tests.test_license_manager_status tests.test_main_startup tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_invalid_license_only_enables_free_tabs tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_valid_license_enables_all_tabs` passed.
- `python -m py_compile main.py core\\feature_access.py license\\manager.py license\\__init__.py gui\\windows\\main_window.py tests\\core\\test_feature_access.py tests\\test_license_manager_status.py tests\\test_main_startup.py tests\\gui\\test_main_window_shortcuts.py` passed.
