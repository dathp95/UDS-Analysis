---
name: python-uds-analyzer
description: Project workflow for the Python UDS Analyzer repository. Use when Codex works on ASC/BLF log parsing, ISO-TP reassembly, UDS request/response matching, ECU mapping, transaction and report generation, Excel export, PySide6 GUI/controller/presenter code, repository rules, agent skills, Git preparation, or any task where behavior must be preserved unless the user explicitly asks for logic changes.
---

# Python UDS Analyzer

## Core Rule

Preserve code behavior by default. Do not modify runtime logic unless the user explicitly requests a logic change. For rules, skills, Git setup, documentation, or repository hygiene tasks, edit only the relevant non-runtime artifacts.

## First Reads

Read `AGENTS.md` first. Then read `references/project-map.md` when the task touches project structure, runtime behavior, reports, GUI, or Git hygiene.

For runtime tasks, inspect the directly relevant files before editing:

- Entry point: `main.py`
- Pipeline: `core/pipeline.py`
- Parsing: `core/asc_reader.py`, `core/convert_blf.py`
- Transactions: `core/build_transactions.py`, `core/uds_lookup.py`, `core/ecu_mapping.py`
- Reports/export: `core/report_engine.py`, `core/report_export.py`, `core/export_transactions.py`
- GUI flow: `gui/windows/main_window.py`, `gui/controllers/`, `gui/presenters/`, `gui/widgets/`
- Config: `config/paths.py`, `config/settings.json`, `config/uds_config.json`, `config/ecu_config.xlsx`

## Workflow

1. Restate the intended scope in your own words.
2. Read the smallest set of files that can answer the task.
3. Identify whether the request allows runtime logic edits.
4. If logic edits are not explicitly allowed, confine changes to rules, skills, docs, Git metadata, or other non-runtime files.
5. Make narrow edits that match existing project style.
6. Verify with the lightest useful command.
7. Report changed files, verification, and any blocker.

## Behavior Boundaries

Treat these as behavior-sensitive:

- parsing ASC/BLF frames
- ISO-TP reassembly
- UDS service, DID, routine, sub-function, NRC, and timeout matching
- ECU request/response CAN ID mapping
- transaction status rules: `PASS`, `NRC_ONLY`, `TIMEOUT`
- report summary fields and Excel sheet structure
- GUI button state, filtering, export, and theme behavior

Do not rename keys in transaction, report, or table dictionaries unless the user asks for that breaking change.

## Git Workflow

When asked to link or push this project:

1. Check whether Git is installed and whether `.git` exists.
2. Create or preserve `.gitignore` so local environments, caches, logs, and generated output are not committed.
3. Initialize the repository only if `.git` is absent.
4. Set remote `origin` to the requested GitHub repository.
5. Stage intended project files only.
6. Commit with a concise message.
7. Push to the requested branch.

If Git is missing, GitHub returns 404, or authentication is unavailable, prepare the files and report the exact blocker instead of inventing success.

## Verification Hints

For rule/skill changes:

```powershell
python C:/Users/LENOVO/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/python-uds-analyzer
```

For a repository snapshot when Git is available:

```powershell
git status --short
git remote -v
```

For runtime checks, only when logic changes were requested:

```powershell
python -m compileall core gui config main.py
```
