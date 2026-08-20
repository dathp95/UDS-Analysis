# CAN Interface Tab

## Summary

- Added a new `CAN Interface` tab after `CRC_Converter` and before `Vehicle Manager`.
- Added CAN service architecture under `services/can`:
  - `CANConfig` dataclass.
  - `CANService` for validation and clean public APIs.
  - `VectorBackend` for `python-can` Vector bus open/close logic.
- Kept `python-can` import lazy inside the backend so the app can start without Vector hardware or driver connected.
- Added UI controls for Vendor, Device, Channel, Baudrate, Refresh, Connect, Disconnect, and status states.
- Added `Feature.CAN_INTERFACE` to central feature access policy and treated it as a licensed feature.
- Added unit tests for CAN service validation and CAN Interface tab behavior.

## Verification

- `python -m py_compile main.py core\feature_access.py gui\windows\main_window.py gui\tabs\can_interface_tab.py services\can\can_config.py services\can\can_service.py services\can\vector_backend.py`
- `python -m unittest tests.services.test_can_service tests.gui.test_can_interface_tab tests.core.test_feature_access`
- `python -m unittest tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_coding_value_tab_is_next_to_log_analyzer tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_can_interface_tab_is_available_after_crc_converter tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_invalid_license_only_enables_free_tabs tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_valid_license_enables_all_tabs tests.gui.test_main_window_shortcuts.MainWindowShortcutTests.test_shortcuts_only_run_on_log_analyzer_tab`
- Offscreen MainWindow startup check printed `CAN Interface`.

## Notes

- Full `tests.gui.test_main_window_shortcuts` still has an unrelated existing failure in `test_license_support_tab_shows_support_and_contact_content`: the test expects `continued development`, while current UI text is `Enjoying the tool? Buy me a coffee!`.
- `DocDiagnostic/VFDSVAEEP0002_Basic_DID_PID_Specification_V1.3.pdf` appeared deleted in git status, but this task did not modify that file.
