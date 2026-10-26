# M05B / Commit 63 - Portable Vehicle ECU DLL resources

Baseline: commit 62, `de1a8c39b7b03ace728accf09e32a4a14525b083`.
The existing Vehicle Manager Browse -> Save is the only DLL selection workflow.
No OEM DLL was executed, no live Security Access was enabled, and no commit/push was made.

## Saved configuration and portability

New import example, relative to `VehicleRepository.root`:

```
VF5NP/resources/dll/BCM/BCM.dll
VF6/resources/dll/BCM/BCM.dll
```

Each ECU JSON uses its existing resources mapping:

```json
{"dll": "resources/dll/BCM/BCM.dll", "dll_path_base": "vehicle"}
```

The optional base marker is required to avoid silently changing M05A relative-path
semantics. The DLL field remains the sole saved path; the marker is context, not a
second registry. Other resources, unknown keys, CAN IDs, aliases and quick requests survive.

| Reference | Resolution |
|---|---|
| Relative + `dll_path_base=vehicle` | Repository root / Vehicle / reference; exact `resources/dll/<selected ECU>/<file>` layout |
| Relative with no marker, or explicit `project` | V-CODE application root / reference, including legacy `resources/dll/...` strings |
| Existing local absolute path | Existing external file; no implicit import |
| Unknown base, traversal, drive-relative/rooted/UNC/device/URI value or linked managed path | Friendly invalid-path/error status; no execution |

No existence-based fallback searches arbitrary folders. New imported JSON never stores
the source absolute path. Moving the V-CODE directory preserves the new references because
the repository/application roots relocate with it. Absolute external references retain
their old semantics and may become missing on another PC. x86 compatibility and external
dependencies do not become portable executable capabilities merely because a file moved.

## Browse, Save and read-only CAN flow

Browse uses the existing native DLL picker and static PE inspector. It changes the draft
only; Cancel preserves it. Valid x86 DLLs can be imported on x64 while showing that a future
32-bit helper is needed. Saving an unchanged legacy reference does not copy it. Explicit
Browse of that same absolute filename still requests import; editing the path also counts
as an explicit update. Selection/reload resets import intent.

Save passes optional import intent through VehicleController -> VehicleService ->
VehicleRepository. Reload displays the portable path and saved static metadata, then emits
the existing Vehicle change event. CAN Interface resolves the saved Vehicle/ECU through
the existing resolver and resource controller; there is no CAN-side picker or store.
Metadata refresh preserves completed diagnostic payloads/results and request generation
when ECU addressing is unchanged. Existing Vehicle/address changes retain invalidation.
Neither export names nor file presence authorize a key calculation or any UDS request.

## Integrity, transactions and recovery

1. A cooperative exclusive repository writer lock covers import/Save/Add/Delete ECU,
   Delete Vehicle, reference scanning and cleanup. An additional import marker localizes
   an interrupted import to its Vehicle. Competing writers fail clearly rather than race.
2. Validate the source using bounded static PE inspection. Create a unique temporary
   DLL in the destination ECU directory. Copy in 64 KiB blocks while hashing SHA-256;
   compare original, copied stream, copied file and source recheck hashes. Revalidate
   copied PE metadata before publication. The existing 16 MiB/512-export limits apply.
3. Reuse an identical existing destination. A differing basename gets a deterministic
   `<sanitized-stem>-<SHA256 first 16 hex>.dll` version. If that name also conflicts with
   different content, abort. Never silently overwrite a different existing DLL.
4. Publish a new copy with same-directory `os.replace` after validation, then publish
   JSON using fsynced temporary files and atomic replacement. Failed JSON operations
   restore original bytes/references and remove only the newly published DLL/temp files.
5. A managed-resource rename commits the new ECU JSON, updated Vehicle list and removal
   of the old ECU JSON in one handled-failure transaction. The GUI skips its old redundant
   Delete call after that transaction. Case-only rename is rejected before writes because
   Windows aliases those JSON filenames. Plain legacy rename retains its existing flow.
6. A changed managed reference is revalidated inside the writer lock. A stale draft cannot
   restore a collected DLL and then delete the current valid copy. Missing unchanged legacy
   references remain editable for unrelated fields, as in M05A.
7. After commit, collect only the formerly referenced managed file if no resource in any
   Vehicle still references it. External/legacy source files are never collected. Remove
   only empty managed directories. Delete ECU follows the same rule; Delete Vehicle is
   blocked if another Vehicle references its files, otherwise its directory is removed.
8. If rollback itself fails, retain all DLL copies, keep writer/import locks, emit an explicit
   incomplete-rollback error, and attempt `.json.recovery` snapshots of original JSON.
   If even recovery writes fail, the error still reports incomplete rollback. Review current
   JSON, available snapshots and DLLs before restoring configuration and manually removing
   stale locks. A cleanup failure after commit is explicitly reported as "configuration saved,
   cleanup failed"; the GUI reloads/notifies instead of reporting a normal successful Save.

Handled exceptions are covered; this is not a power-loss-atomic multi-file filesystem
transaction. A hard process kill can leave locks, staging/unreferenced files, or an intermediate
rename index. Publication order retains valid copies and uses atomic individual JSON writes;
locks require manual recovery review instead of silently resuming. Non-cooperating external
editors can bypass the lock. Imported DLLs, staging copies, locks and recovery JSON are covered
by targeted git ignores; existing JSON configuration and synthetic fixtures remain trackable.

## Mock provider and future isolated x86 IPC

`services/seed_key_provider.py` defines immutable typed request/response objects,
`SeedKeyProvider` and `WorkerTransport` protocols, bounded codecs and a deterministic fake.
The fake simulates the worker through serialized messages **in memory**; no x86 subprocess,
native loader or OEM implementation is present. It is not connected to CAN controllers.

| Request fields | Contract |
|---|---|
| `version` | Exactly integer 1 |
| `request_id` | 1-64 ASCII letters/digits/underscore/hyphen; response must correlate exactly |
| `vehicle`, `ecu` | Nonempty text, at most 128 characters, no control characters |
| `level` | Integer 1-127; no transmission implied |
| `seed_hex` | Hex bytes, 1-64 decoded bytes |
| `output_size` | Integer 1-64 bytes |
| `timeout_ms` | 1-30000 ms; parent deadline/cancellation remains authoritative |

Success response: version, matching request_id, status `ok`, bounded `key_hex` of the exact
requested length and `mock_only=true`. Error response: version, matching request_id,
status `error`, finite `error_code`, mock_only; no key or arbitrary worker error text.
Maximum JSON frame is 4096 bytes; reject duplicate/unknown fields, invalid encodings,
wrong IDs, unexpected versions and non-mock responses. Errors map to bad request/response,
timeout, cancellation, worker crash and unavailable. Seed/key fields are excluded from repr;
the provider emits no logs, and errors contain only fixed messages/codes. Never log wire data.

A future separately reviewed x86 process adapter must use length-prefixed, size-bounded
private local IPC, one outstanding correlated request per worker, a parent hard deadline,
cancellation/worker termination and reaping. EOF/crash -> worker_crash, expiry -> timeout,
cancel -> cancelled, malformed/mismatched reply -> bad_response; late replies cannot complete
another request. Clear sensitive buffers where feasible, restrict process/pipe access and
never include seed/key data in diagnostics. Real implementation must require OEM-authorized
ABI details: calling convention, integer/pointer widths, parameter layout, output ownership,
return-code semantics and verified test vectors. GenerateKeyEx's name is insufficient.
No supplied OEM DLL was loaded, no secret extracted and no `27 01`/`27 02` was sent.

## Verification

Actual commands (local ignored QA runner also isolates default UI preferences and blocks
inspection of real external DLL references in legacy GUI tests):

```powershell
.venv\Scripts\python.exe output/qa_can_m05b/run_validation.py m5b
.venv\Scripts\python.exe output/qa_can_m05b/run_validation.py can
.venv\Scripts\python.exe output/qa_can_m05b/run_validation.py vehicle
.venv\Scripts\python.exe output/qa_can_m05b/render_ui.py
git diff --check
git check-ignore --no-index config/vehicles/VF5NP/resources/dll/BCM/BCM.dll config/vehicles/VF6/resources/dll/BCM/BCM.DLL
```

Focused suite modules: `tests.services.test_vehicle_dll_storage`,
`tests.services.test_seed_key_provider`, `tests.services.test_dll_resource`,
`tests.gui.test_ecu_dll_resource`, `tests.gui.test_vehicle_dll_integration`.

| Suite | Run | Passed | Failed | Errors / skipped |
|---|---:|---:|---:|---:|
| M05A/M05B focused tests | 36 | 36 | 0 | 0 / 0 |
| CAN M01-M04B, manual policy, Commit 60-62 regressions | 254 | 254 | 0 | 0 / 0 |
| Vehicle service/export/selector regressions | 43 | 42 | 1 baseline | 0 / 0 |
| Distinct total | 333 | 332 | 1 baseline | 0 / 0 |

The pre-existing failure is
`VehicleSelectorWidgetTests.test_vehicle_manager_has_display_names_import_button`:
expected `Import Display Names`, actual baseline `Import File Display Names`. Reproduced
against commit 62 VehicleManagerTab compiled in memory from `git show HEAD`, without changing
source. No unrelated label fix was made. All 12 changed/new Python files compiled successfully.

Coverage includes VF5NP/VF6 Browse/Save isolation, separate copies, relocation + changed CWD
without source directory, legacy references including overlapping prefixes, draft/Cancel,
missing/corrupt/large/x86 DLLs, checksum/copied-PE/version conflicts, symlink escape guard,
atomic/JSON/rename/rollback failures, incomplete recovery, stale draft, shared references,
writer races, Save metadata refresh/result preservation, theme/restart, disabled SecurityAccess,
and fake correlation/timeouts/in-flight cancellation/crash/size limits/redaction/no native loaders.
On Windows without symlink creation permission, the link predicate is simulated for that guard.

Offscreen PySide screenshots were visually checked with Segoe UI in Light/Dark at 1366x768
and 1600x900. Portable path, status and existing layout remain readable. No hardware, native
dialog interaction or real OEM DLL execution was tested. QA JSON/images are in ignored
`output/qa_can_m05b/`. Independent review found writer/cleanup races, case-only rename,
cross-Vehicle Delete dependencies and stale drafts; fixes have deterministic regressions.

## Modified files

- `.gitignore`: local imported binaries/staging/locks/recovery exclusions.
- `core/vehicle_dll_paths.py`: explicit path-base and confinement contract.
- `repositories/vehicle_dll_storage.py`: locks, hash/copy/publication and JSON rollback helpers.
- `repositories/vehicle_repository.py`: import/Save/rename/lifecycle integration.
- `services/vehicle_service.py`: import intent, rename and saved reference validation.
- `services/ecu_dll_resource.py`: saved path-base-aware read-only metadata.
- `services/seed_key_provider.py`: mock-only typed provider/IPC foundation.
- `gui/controllers/vehicle_controller.py`: import forwarding and metadata accessor.
- `gui/widgets/vehicle_manager/ecu_resource.py`: draft intent and saved metadata display.
- `gui/tabs/vehicle_manager_tab.py`: import-on-Save, transactional rename result and error UX.
- `tests/services/test_vehicle_dll_storage.py`: portable/integrity/rollback/lifecycle regressions.
- `tests/services/test_seed_key_provider.py`: bounded mock IPC/error/redaction tests.
- `tests/gui/test_vehicle_dll_integration.py`: existing M05A assertions updated for portable Save,
  plus GUI intent/rename/failure/isolation coverage.
- `tasks/plan.md`, `tasks/todo.md`: implementation decisions and verification checkpoints.
- `docs/can_interface/M05B_PORTABLE_VEHICLE_DLL_REPORT.md`: this report.

Pre-existing user changes to CAN UI preferences and the new skill were preserved. Native
Vector ownership, ISO-TP, CAN Monitor, BLF, connection authorization and diagnostic 0x27
policy files were not changed. Static inspection remains bounded but synchronous; slow local
storage can delay Save. Windows path/permission/dependency limits still apply. Redistribution
rights must be established separately; imported proprietary binaries are not release assets
by default. File metadata is never proof of ABI, trust or execution permission.

Suggested commit: `can interface - commit 63: Portable Vehicle ECU DLL Resources`.
