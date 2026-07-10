---
description: Core guardrails that apply to every agent task in this repository
alwaysApply: true
fileMatching: "**/*"
---

# Core Guardrails

These rules apply to the whole Python UDS Analyzer repository.

## Non-Negotiable Rules

- Preserve application behavior by default.
- Do not change runtime code logic unless the user explicitly asks for a logic change.
- Do not refactor, rename, reformat, or reorganize runtime code as a side effect of rule, skill, Git, documentation, or analysis tasks.
- Do not delete user files, logs, generated reports, configs, workbooks, or local settings unless the user explicitly asks.
- Do not overwrite existing user edits. If unrelated edits are present, work around them or ask before touching that file.
- Keep changes narrowly scoped to the current request.
- Prefer reading local context before editing.

## Runtime-Sensitive Behavior

Treat these as behavior-sensitive:

- ASC and BLF parsing
- ISO-TP reassembly
- UDS service, DID, routine, sub-function, NRC, and timeout matching
- ECU request and response CAN ID mapping
- transaction statuses: `PASS`, `NRC_ONLY`, `TIMEOUT`
- report summary fields and Excel workbook sheet structure
- GUI button state, filtering, export behavior, and theme behavior

Do not rename transaction, report, table, or config keys unless the user explicitly asks for a breaking contract change.

