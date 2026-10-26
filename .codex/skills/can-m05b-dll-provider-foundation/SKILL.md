---
name: can-m05b-dll-provider-foundation
description: Implement Commit 63 portable, per-Vehicle/per-ECU DLL import in V-CODE and mock-only Seed-Key provider foundation; preserve CAN diagnostics, never execute OEM DLL or live UDS 0x27.
---

# Commit 63 — Portable Vehicle DLL Storage (M05B)

## Baseline and purpose

Repository: `dathp95/UDS-Analysis`; baseline commit 62 `de1a8c39b7b03ace728accf09e32a4a14525b083`. Inspect current working tree and respect newer uncommitted changes before editing.

**User decision (authoritative):** Vehicle Manager is the single place to Browse and Save ECU DLLs. Upon saving a newly selected DLL, import a COPY into that Vehicle's own ECU-specific directory, and make the saved reference portable when the entire V-CODE folder is moved to another machine. `VF5NP/BCM` and `VF6/BCM` must never share or overwrite each other's DLL. Existing external-path references must remain readable for compatibility, but newly selected DLLs follow the import-on-Save workflow. No separate CAN Interface Browse.

## Existing sources to reuse

- `models/ecu.py`: `ECU.resources['dll']` is the only authoritative saved reference.
- `gui/widgets/vehicle_manager/ecu_resource.py`: DLL field, Browse button, static PE inspection.
- `gui/tabs/vehicle_manager_tab.py`: ECU Save path and `vehicle_data_changed` signal.
- `repositories/vehicle_repository.py`: Vehicle and ECU JSON persistence.
- `services/vehicle_service.py`: Save/Load ECU and resource validation.
- `core/dll_resource.py`: bounded static PE validation/architecture/exports, NEVER DLL execution.
- `services/ecu_dll_resource.py`, `gui/controllers/can_dll_resource_controller.py`: read-only resource resolution and status in CAN Interface.
- Existing diagnostic/Vector/CAN Monitor/BLF behavior and 0x27 restriction remain unchanged.

## A. Destination folder and path contract

Use destination pattern beneath `VehicleRepository.root`:

```
config/vehicles/
  VF5NP/
    vehicle.json
    ecus/BCM.json
    resources/dll/BCM/BCM.dll
  VF6/
    vehicle.json
    ecus/BCM.json
    resources/dll/BCM/BCM.dll
```

- Store `resources['dll'] = 'resources/dll/BCM/BCM.dll'` in `VF5NP/ecus/BCM.json`. **Relative paths for newly imported DLLs are relative to the Vehicle directory**, not the ECU JSON folder and not the process current working directory.
- Resolve using `VehicleRepository.root / vehicle_name / relative_resource_path`; protect against `..`, absolute injection, Windows drive-relative values, UNC/device paths and symlink escapes.
- Compatibility: continue resolving legacy absolute references; handle legacy project-root-relative paths without silently changing their meaning. Choose an explicit, unambiguous resolution/migration policy; document it and cover it in tests (do not guess relative-path base just by trying arbitrary directories).
- Never store source absolute paths in the new imported ECU configuration; moving the whole V-CODE folder to another path must not break references.
- This is application-portable configuration, **not** proof that x86 DLLs run directly in a 64-bit app or that driver dependencies are bundled.

## B. Vehicle Manager Browse → Save workflow

1. On Browse use native file picker limited to `.dll`; Cancel leaves the current value and saved resource unchanged. Show selected filename/path and static metadata (machine, bitness, exports, valid/invalid state). Browse itself does not copy or execute the DLL.
2. On Save for a newly selected DLL, validate it via `inspect_dll_resource`. Permit structurally valid x86 PE DLL despite x64 incompatibility with in-process loading; show that a future x86 helper is required.
3. Ensure destination directory is based on the **selected Vehicle and ECU** and a sanitized filename. Never overwrite another Vehicle or ECU's contents.
4. Copy through a temp file *in the destination directory*, calculate SHA-256 by streaming, check source and copied file integrity, and revalidate copied PE metadata. Perform atomic replace only after all checks pass; on failure retain old saved JSON/DLL reference and delete temporary files.
5. If replacing an existing different DLL, use a clear explicit overwrite confirmation or a safe versioned-file strategy. Do not silently destroy an existing copy used by another resource. Avoid half-finished saves if JSON persistence fails; document transaction/recovery behavior.
6. Preserve ECU fields and unrelated `resources` keys (`dbc`, `odx`, `dtc`, `request_library`), CAN IDs, quick requests, sequence results and Vehicle selection. Do not import a legacy external reference until the user explicitly selects/updates it through Browse and Save.
7. After Save, reload the ECU and display the saved portable path and validated metadata. Emit existing Vehicle resource changed notification so CAN Interface refreshes the status of the selected ECU without invalidating unrelated step results.
8. When ECU is renamed/deleted or Vehicle deleted, ensure no orphaned or misassociated DLL path remains; document and test appropriate lifecycle behavior.

## C. CAN Interface consumption

- Keep Vehicle Manager/VehicleRepository as one source of truth; CAN Interface must resolve the saved `Vehicle + ECU` pair, not a basename-only lookup.
- Status can report filename, architecture and `GenerateKeyEx` export **as static metadata only**. Never claim a real key calculation or successful Security Access.
- If resource missing or moved, show a clear failure status without crashing.
- Do not add a CAN-side DLL picker, preference store, hardcoded `BCM.dll` directory, or duplicated path registry.

## D. Seed-Key provider foundation — mock only

- Define a typed, easily testable provider interface and a deterministic **fake** for tests. Document isolated x86 worker IPC (request ID, ECU/level, input/output size limits, timeout, cancellation, worker crash/error mapping, no seed/key logging).
- Future DLL loader requires OEM-authorized ABI specification for `GenerateKeyEx` (parameters, widths, calling convention, output ownership, return codes) and verified seed-key test vectors. An exported symbol is NOT an ABI specification.
- Do not load/run the supplied production BCM.dll, reverse-engineer proprietary secrets, implement a live unlock path, transmit `27 02`, enable `27 01` sending, or bypass existing authorization. Keep `core/diagnostic_request.py` SecurityAccess 0x27 restrictions intact.
- Do not commit OEM DLLs to git by default. Add targeted ignores for imported binary files while retaining JSON config and safe test fixtures. Verify redistribution permission separately.

## E. Tests and acceptance

1. VF5NP/BCM Browse then Save creates `config/vehicles/VF5NP/resources/dll/BCM/BCM.dll`; JSON uses `resources/dll/BCM/BCM.dll`.
2. VF6/BCM gets its own physically separate copy; its DLL and JSON remain untouched when VF5NP changes.
3. Copy/move entire V-CODE root to another folder, change CWD, re-open app/service, and resolve both DLLs without original source folder.
4. Existing absolute-path references continue to work; legacy relative paths use documented compatibility policy.
5. Cancel Browse, invalid or missing DLL, corrupt PE, unsupported architecture (x86 on x64), too large, symlink traversal, duplicate/overwrite conflict, copy/checksum/JSON failure leave a valid state.
6. CAN Interface correctly reads per-Vehicle/per-ECU metadata and refreshes on Save; cannot leak results/DLL between ECUs.
7. Fake provider tests: correlation, timeout, cancellation, size bounds, crash, redaction.
8. Verify GUI/theme/restart behavior; run existing M04/M04B CAN, ISO-TP, BLF, diagnostic/manual policy, Commit 60-62 and Vehicle Manager regression suites. Report *actual* counts and any baseline failures without inventing results.

## Deliverables

- Minimal changes and focused tests.
- `docs/can_interface/M05B_PORTABLE_VEHICLE_DLL_REPORT.md` specifying path base, migration, transaction/rollback decisions, tests and limits.
- Summary of modified files and precise test commands/outcomes.
- **Do not commit or push automatically.** Proposed commit title: `can interface - commit 63: Portable Vehicle ECU DLL Resources`.
