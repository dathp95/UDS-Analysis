# M05B implementation plan (commit 62 baseline)

## Commit 64 implementation (baseline 37e0f1b)

Authoritative specification: `.codex/skills/can-sequence-editor-commit64/SKILL.md`.
1. Pure bounded TSV/quoted CSV codec and validation tests; results are informational only.
2. Fixed two-row sidebar footer and native draft document/controller/dialog actions;
   restore sequence-name column, retain stable step IDs and unresolved ECU diagnostics.
3. In-memory per-Vehicle/ECU field snapshots, including explicit DLL import intent;
   dirty indicators and scoped discard/save/delete/rename lifecycle.
4. Focused tests, CAN/UDS/BLF/portable DLL regressions, Light/Dark visual checks, report.
No CAN transport/security execution changes or commits. Protect pre-existing Vehicle JSON
edits with before/after hashes. Tests use temporary configs and synthetic PE fixtures.

The user-approved M05B skill is the specification and acceptance contract. Implement
portable per-Vehicle/per-ECU import on explicit Browse/update + Save; no OEM execution.

1. Path and storage slice: new imports use `resources/dll/<ECU>/<file>` plus the
   `resources.dll_path_base=vehicle` marker. Unmarked relative paths retain project-root
   semantics even if their prefix matches the new namespace. Retain absolute legacy references. Test isolation,
   relocation, invalid paths, checksums, version conflicts and rollback first.
2. GUI slice: explicit import intent through existing Controller -> Service -> Repository;
   Browse does not copy. Reload saved portable references and resolve static metadata.
   Test Save/Cancel/restart and resource-only refresh preserving completed diagnostics.
3. Mock provider slice: typed bounded IPC/correlation/errors, deterministic fake only,
   no loader or transport integration. Test timeout/cancellation/crash/redaction.
4. Review and verification: M04/M04B/60-62 regression, static PE fixtures only, Light/Dark
   render, compile/diff checks, report exact results and remaining recovery limits.

Storage decisions: version conflicting filenames, atomic same-directory publication,
streamed SHA-256 + copied PE revalidation, transactional JSON snapshots/rollback. Rename
imports the managed reference into the new ECU directory; deletion collects only formerly
referenced managed files after configuration commit and checks remaining references.
Do not touch native CAN ownership, authorization, monitor, BLF or 0x27 policy.

Commands: `.venv\Scripts\python.exe -m unittest tests.services.test_vehicle_dll_storage -v`
and focused GUI/provider suites, followed by the existing regression suites. Python
unittest and synthetic PE fixtures follow existing repository style. No dependency/schema
changes, OEM binary commits, automatic commit/push, or access to licensing/key material.
