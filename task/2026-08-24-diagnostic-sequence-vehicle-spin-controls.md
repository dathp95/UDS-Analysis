# Diagnostic Sequence Vehicle Selector + Spin Controls

Date: 2026-08-24

## Scope

Updated the Diagnostic Sequence execution row in the CAN Interface tab. No CAN/UDS execution logic, JSON schema, DiagnosticSequenceRepository, or CAN backend changes were made.

## Changes

- Added reusable `PrimarySpinBox` and centralized `spinbox_style`.
- Extended `VehicleSelectorWidget` with optional horizontal orientation while preserving the default vertical layout used by existing tabs.
- Added Vehicle selector to the Diagnostic Sequence execution row using the same `VehicleService.list_vehicles()` source as Log Analyzer.
- Added `fn_refresh_vehicles()` and `fn_current_vehicle()` to `DiagnosticSequenceTable`.
- Replaced Loop text input with `PrimarySpinBox` range `1..9999`, step `1`.
- Replaced Command Delay text input with `PrimarySpinBox` range `0..60000`, step `100`, while still allowing manual values such as `150`.
- Kept `EXPORT`, `STOP`, `RUN` right aligned after one stretch.
- Kept vehicle selection separate from diagnostic sequence JSON/model persistence.

## Verification

- `python -m unittest tests.repositories.test_diagnostic_sequence_repository tests.gui.test_diagnostic_sequence_list tests.gui.test_diagnostic_sequence_table tests.gui.test_can_interface_tab tests.test_main_startup tests.gui.test_vehicle_selector.VehicleSelectorWidgetTests.test_can_leave_vehicle_unselected tests.gui.test_vehicle_selector.VehicleSelectorWidgetTests.test_vehicle_popup_uses_opaque_background`
- `python -m py_compile gui\\themes\\styles\\controls\\spinbox_style.py gui\\widgets\\controls\\primary_spinbox.py gui\\widgets\\vehicle_manager\\vehicle_selector.py gui\\widgets\\diagnostic\\diagnostic_sequence_table.py tests\\gui\\test_diagnostic_sequence_table.py gui\\tabs\\can_interface_tab.py`
- `git diff --check`

All listed checks passed.
