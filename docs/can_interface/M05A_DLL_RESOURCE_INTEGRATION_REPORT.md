# M05A - Vehicle Manager DLL resources

Baseline: commit 61, `b9f6e980c7c14ad95d07f9cbfcbd63a60c557822`.
Scope: configuration, persistence and static metadata only. No DLL loader, function
invocation, Seed-Key calculation or Security Access execution was added. No commit/push.

## Data flow and decisions

1. Existing Vehicle Manager DLL Browse opens a native `*.dll` dialog. Cancel leaves
   the draft unchanged. Valid selection fills the existing path field and tooltip.
   Invalid selection shows a non-modal status and retains the previous field value.
2. `ECUResourceWidget` statically inspects the draft and returns a new ECU with a copied
   resources mapping. It does not mutate the selected source ECU. Selection changes
   discard the resource draft. Other resource fields and unknown resource keys survive.
3. Existing Save uses VehicleController -> VehicleService -> VehicleRepository.save_ecu.
   A changed, nonempty DLL reference must pass static validation. Existing missing or
   legacy paths do not prevent unrelated saves; clearing a reference is allowed.
   Existing per-ECU resources JSON is reused without a schema change or second store.
4. `VehicleService.resolve_ecu_dll_resource(vehicle_name, ecu_name)` and its narrow
   helper resolve the authoritative saved ECU through the same Vehicle/ECU selector
   used by diagnostic TX/RX resolution. They return immutable metadata with separate
   unconfigured, missing, invalid, malformed, unsupported architecture and available states.
5. CAN Interface displays a compact read-only status for the selected row's ECU.
   Tooltip shows basename, architecture, up to 16 export names and the ABI limitation.
   There is no CAN-side Browse, path preference or authorization change. Repeated edits
   of the same ECU's payload/comment do not rescan its file. Vehicle/config/resource
   events invalidate the presentation cache.
6. Vehicle Manager Save refreshes CAN resources. With unchanged Vehicle identity and
   ECU names/TX/RX IDs, completed runtime results, stable step IDs and diagnostic generation
   survive. A changed/missing transport configuration retains existing reset/cancellation
   protections. Loading another sequence still starts a fresh runtime, as commit 60 requires;
   the skill's sequence wording is interpreted consistently with that baseline behavior.

## Paths and static validation

- Absolute local paths remain external references; no DLL is copied into the repository
  or release. Relative legacy paths resolve against V-CODE's application/project root,
  independently of the working directory. A newly edited valid path is displayed/saved
  as its resolved absolute path. Unchanged legacy strings are retained.
- Reject network/device/URI paths, control characters, reserved Windows names,
  drive-relative paths, wrong extension, missing/nonregular/unreadable files.
- Reuse already pinned `pefile==2024.8.26` with fast-load and export-directory-only parsing.
  Bound inspection to 16 MiB, 96 sections, 512 exports and 512 bytes per name/forwarder;
  check DLL headers, machine/bitness consistency and named export ordinals/tables.
- x86 DLL metadata can be saved on x64 but is explicitly reported incompatible and
  requiring a future 32-bit helper. Missing GenerateKeyEx is reported rather than guessed.
  An export name never proves a callable signature, calling convention or authorization.
- No PE bytes, seeds, keys or OEM materials are logged/committed. CAN default text and
  tooltips omit absolute paths; the Vehicle Manager path field intentionally shows them.

## Modified files

| File | Change |
|---|---|
| `core/dll_resource.py` | Immutable status/metadata and bounded static PE inspection |
| `services/ecu_configuration.py` | Shared authoritative Vehicle/ECU selection |
| `services/ecu_dll_resource.py` | Read-only saved DLL resolver |
| `services/vehicle_service.py` | Public resolver; changed-path Save validation |
| `services/can/ecu_diagnostic_resolver.py` | Reuse shared ECU selection, retain transport checks |
| `gui/widgets/vehicle_manager/ecu_resource.py` | Existing Browse wiring, feedback, isolated resource draft |
| `gui/tabs/vehicle_manager_tab.py` | Consume validated draft through existing Save |
| `gui/controllers/can_dll_resource_controller.py` | Selected ECU metadata presentation and refresh |
| `gui/widgets/can_interface/current_test_case_panel.py` | Themed read-only DLL status |
| `gui/widgets/can_interface/diagnostic_table_panel.py` | Separate resource refresh from transport invalidation |
| `gui/controllers/can_workspace_controller.py` | Preserve results during unchanged resource refresh |
| `gui/tabs/can_interface_tab.py` | Compose metadata controller |
| `tests/dll_fixture.py` | Synthetic PE bytes; no executable implementation |
| `tests/services/test_dll_resource.py` | Static parser bounds/status/no loader tests |
| `tests/gui/test_ecu_dll_resource.py` | Browse/Cancel, draft isolation and legacy resources |
| `tests/gui/test_vehicle_dll_integration.py` | Actual Save/reload/refresh/theme/0x27 integration |
| `docs/can_interface/M05A_DLL_RESOURCE_INTEGRATION_REPORT.md` | This report |

User's pre-existing `config/can_interface_ui.json` edit and untracked skill were preserved.
Vector ownership, transport, monitor, recording and bench authorization code are untouched.

## Verification

| Suite | Run | Passed | Failed | Errors / skipped |
|---|---:|---:|---:|---:|
| M5A new tests | 14 | 14 | 0 | 0 / 0 |
| CAN M01-M04B and commits 59-61 regression | 254 | 254 | 0 | 0 / 0 |
| Vehicle service/export/selector regression | 43 | 42 | 1 existing | 0 / 0 |
| Total distinct tests | 311 | 310 | 1 existing | 0 / 0 |

The existing failure is
`VehicleSelectorWidgetTests.test_vehicle_manager_has_display_names_import_button`:
test expects `Import Display Names`, baseline UI says `Import File Display Names`.
Reproduced by compiling `git show HEAD:gui/tabs/vehicle_manager_tab.py` in memory and
running that same test against the baseline class. No unrelated label was changed.

New tests cover Browse/Cancel, invalid extension/corrupt/truncated/unreadable PE,
malformed export tables, no GenerateKeyEx, x86/x64, immutable metadata, null/missing
resources, restart via fresh controller/service/repository, ECU/Vehicle isolation,
CAN IDs/other resources unchanged, saved-event delivery to the composed CAN tab,
completed response and generation preservation, changed CAN ID invalidation,
Light/Dark refresh without data mutation, and the existing disabled 0x27 row action.
ctypes loaders are patched to fail in static metadata tests.

QA runner uses temporary default UI preferences and blocks inspection of real external
DLL references in legacy tests; only synthetic temporary DLLs are inspected. Command
groups use unittest on `tests.services.test_dll_resource`,
`tests.gui.test_ecu_dll_resource`, `tests.gui.test_vehicle_dll_integration`, existing
`tests.gui.test_can_*`/CAN service/ISO-TP/BLF/sequence suites and Vehicle regressions.
Local runner/result JSON and rendered images are under ignored `output/qa_can_m05a/`.
Offscreen PySide rendering was visually checked with Segoe UI in Light/Dark at
1366x768 and 1600x900; resource path/status/Browse remain readable. `git diff --check`
and Python compilation passed. Independent review agent could not start due to
model capacity; local source/diff review and deterministic tests were completed.

## Limitations and future boundary

- No Vector hardware or real OEM DLL execution was tested. All DLL tests use synthetic
  static PE fixtures. UI rendering is offscreen, not physical native-dialog interaction.
- Static metadata does not validate ABI, signatures, behavior or trust. Inspection is
  synchronous and bounded; slow local storage can still delay feedback. Files over the
  stated budgets are reported unsupported/malformed rather than partially trusted.
- No file watcher: an externally moved/changed file is observed on selection/configuration
  refresh or Vehicle Manager validation, not continuously. File content may change after
  inspection, so future execution must independently reopen/revalidate the actual file.
- A future reviewed x86 helper must run outside the V-CODE process, verify the documented
  vendor ABI/calling convention, bound IPC/timeouts and validate outputs. No signature is
  inferred from GenerateKeyEx. Any future 0x27 execution needs separate explicit policy,
  testing and authorization; M5A does not implement or authorize it.

Suggested title: `can interface - commit 62: Reuse Vehicle Manager Seed-Key DLL Resources`.
