---
name: vehicle-dll-resource-integration
description: Integrate per-ECU Seed-Key DLL resource selection in V-CODE Vehicle Manager and expose validated configuration to CAN Interface without executing the DLL.
---

# V-CODE – Vehicle Manager DLL Resource Integration

## Baseline
Repository `dathp95/UDS-Analysis`, commit 61 `b9f6e980c7c14ad95d07f9cbfcbd63a60c557822`.
Before editing, inspect the actual current branch/diff. Preserve newer user work. Do not commit/push automatically.

## Objective
Implement a complete flow: Vehicle Manager → choose Vehicle/ECU → DLL Browse → show selected filename/path and static metadata → Save → persistence via existing ECU resources → CAN Interface resolves the same saved DLL for the selected Vehicle/ECU. Scope is configuration and read-only capability reporting only, NOT security-unlock execution.

## Files to inspect first
- `models/ecu.py` (`ECU.resources['dll']` already exists)
- `gui/widgets/vehicle_manager/ecu_resource.py` (has `txt_dll`, `btn_dll`, `fn_set_ecu`, `fn_get_ecu`)
- `gui/tabs/vehicle_manager_tab.py` (`_on_save_clicked`, `vehicle_data_changed`)
- `services/vehicle_service.py`
- `repositories/vehicle_repository.py` (`resources` JSON)
- `gui/tabs/can_interface_tab.py`
- `services/can/ecu_diagnostic_resolver.py`
- Existing CAN diagnostic and Vehicle Manager regression tests.

## Requirements
1. Wire existing `btn_dll` to `QFileDialog.getOpenFileName` with `DLL files (*.dll)`; handle cancel without changing current value. Avoid duplicate buttons and parallel state.
2. Display full selected path in `txt_dll` (with tooltip), with optional basename/metadata next to it. Do not execute or load the DLL during Browse or Save.
3. Validate file existence, extension, regular file, readable PE headers; reject invalid files with clear non-crashing UI feedback. Recognize PE machine type and exported function names through static inspection only. A static export listing does not prove callable ABI.
4. Preserve current behavior of other resources (`dbc`, `odx`, `dtc`, `request_library`). Do not mutate source ECU model before Save; Cancel/selection switch should not silently save draft.
5. Save through the existing `VehicleController` → `VehicleService` → `VehicleRepository.save_ecu` flow. Persist `resources['dll']` to the specific vehicle/ECU JSON. Backward compatibility with missing/empty resources. Reopen/restart should reload same value.
6. Preserve absolute external paths or an explicit supported relative-path strategy without silently copying a proprietary DLL into the repo/release. Missing/moved DLL must show a friendly warning; no security execution attempted.
7. Provide a reusable, read-only resolver `resolve_ecu_dll_resource(vehicle_name, ecu_name)` through the existing vehicle service or narrow helper. It must use the same authoritative vehicle/ECU definition as CAN TX/RX resolution; distinguish not configured / not found / malformed / architecture unsupported / metadata available.
8. CAN Interface may show `DLL configured`, `DLL missing`, or `DLL incompatible (x86 requires 32-bit helper)` for current Vehicle/ECU; do not add another Browse flow or store another path. Refresh metadata when Vehicle Manager emits vehicle_data_changed; avoid resetting unrelated completed diagnostic results unnecessarily.
9. Do not implement `27 01` → `27 02` sending, call `GenerateKeyEx`, extract OEM secret, or allow security bypass in this milestone. Existing 0x27 block remains until execution is independently reviewed, authorized and tested. Do not change Vector owner, ISO-TP framing, CAN monitor, BLF, bench policy, or unrelated tabs.
10. Never automatically load untrusted DLL in V-CODE process; design a future x86 subprocess boundary in documentation only. Do not guess calling convention/function signature.
11. Never log or commit keys, seeds, DLL file bytes or protected OEM materials. Add path sanitization and maintain privacy of absolute machine paths in user reports.

## Tests
- Browse valid DLL populates visible path; Cancel unchanged.
- Save then reload Vehicle and ECU: same resource path. Reload after restarting controller/repository.
- Different ECU/Vehicle DLL paths stay isolated.
- Invalid extension, nonexistent DLL, corrupt PE, 32-bit metadata, no exported GenerateKeyEx: clear UI states, no crash.
- Existing resource fields and ECU CAN request/response IDs unchanged.
- CAN Interface resolves saved path and refreshed metadata after Vehicle Manager Save; no duplicate config.
- Switching Test Sequence preserves previously valid completed results as specified in commit 60; no side-effects from static DLL metadata refresh.
- Regression tests for Vehicle Manager, CAN Interface, CAN connection, ISO-TP and BLF unaffected.
- If no hardware/DLL executable environment, state clearly that only static tests were run.

## Deliverables
1. Minimal code patch and unit tests.
2. Concise design report with data flow, test summary, risks and future ABI-verification work.
3. Suggested title `can interface - commit 62: Reuse Vehicle Manager Seed-Key DLL Resources`.
4. No automatic commit/push.
