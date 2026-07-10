# AI Rules Generated For Python UDS Analyzer

Generated manually from `ai-rules/*.md` following the `block/ai-rules` standard-mode layout. Keep `ai-rules/` as the source of truth and mirror changes here plus agent-facing files.

# Core guardrails that apply to every agent task in this repository

## Core Guardrails

These rules apply to the whole Python UDS Analyzer repository.

### Non-Negotiable Rules

- Preserve application behavior by default.
- Do not change runtime code logic unless the user explicitly asks for a logic change.
- Do not refactor, rename, reformat, or reorganize runtime code as a side effect of rule, skill, Git, documentation, or analysis tasks.
- Do not delete user files, logs, generated reports, configs, workbooks, or local settings unless the user explicitly asks.
- Do not overwrite existing user edits. If unrelated edits are present, work around them or ask before touching that file.
- Keep changes narrowly scoped to the current request.
- Prefer reading local context before editing.

### Runtime-Sensitive Behavior

Treat these as behavior-sensitive:

- ASC and BLF parsing
- ISO-TP reassembly
- UDS service, DID, routine, sub-function, NRC, and timeout matching
- ECU request and response CAN ID mapping
- transaction statuses: `PASS`, `NRC_ONLY`, `TIMEOUT`
- report summary fields and Excel workbook sheet structure
- GUI button state, filtering, export behavior, and theme behavior

Do not rename transaction, report, table, or config keys unless the user explicitly asks for a breaking contract change.

# Repository structure and ownership map for Python UDS Analyzer

## Project Map

### Application Shape

- `main.py` starts the PySide6 application.
- `core/` owns parsing, UDS lookup, transaction building, report generation, Excel export, and the analysis pipeline.
- `gui/` owns windows, widgets, controllers, presenters, and styling.
- `config/` owns settings, path constants, UDS config, and the ECU mapping workbook.
- `logs/` and `output/` are local runtime or generated data.
- `.codex/skills/python-uds-analyzer/` contains the project skill for agent workflow.
- `ai-rules/` contains the source rules used to maintain agent-facing rule files.

### First Files To Read

For runtime tasks, inspect the smallest relevant set before editing:

- Entry point: `main.py`
- Pipeline: `core/pipeline.py`
- Parsing: `core/asc_reader.py`, `core/convert_blf.py`
- Transactions: `core/build_transactions.py`, `core/uds_lookup.py`, `core/ecu_mapping.py`
- Reports/export: `core/report_engine.py`, `core/report_export.py`, `core/export_transactions.py`
- GUI flow: `gui/windows/main_window.py`, `gui/controllers/`, `gui/presenters/`, `gui/widgets/`
- Config: `config/paths.py`, `config/settings.json`, `config/uds_config.json`, `config/ecu_config.xlsx`

### Data Contracts

Parsed messages use: `timestamp`, `can_id`, `dlc`, `data`.

Completed payloads and request/response records use: `timestamp`, `can_id`, `payload`.

Transactions use: `ecu`, `service_id`, `service_name`, `display_name`, `identifier`, `identifier_name`, `sub_function`, `routine_id`, `routine_name`, `request`, `negative_responses`, `positive_response`, `response_pending_count`, `response_time`, `status`.

Activity table columns use: `No`, `Time(s)`, `Service`, `Activity`, `Request`, `Response`, `RT(ms)`, `Status`, `Pending`.

# Required workflow and verification rules for agent work

## Workflow And Verification

### Default Workflow

1. Restate the intended scope in your own words.
2. Read only the relevant files needed for the task.
3. Decide whether the user explicitly allowed runtime logic changes.
4. If logic edits are not allowed, edit only rules, skills, docs, Git metadata, or other non-runtime artifacts.
5. Make narrow edits that follow the existing project style.
6. Verify with the lightest useful command.
7. Report changed files, verification results, and any blocker.

### Verification By Change Type

- Rule, docs, or skill changes: inspect changed files and validate formatting/frontmatter where possible.
- Git metadata changes: run Git status when Git is available.
- Runtime logic changes, only when explicitly requested: run focused Python checks against known sample logs/configs.
- GUI changes, only when explicitly requested: run the app or provide a clear manual check when a GUI session is unavailable.

### Skill Validation

Use this command when `PyYAML` is available:

```powershell
python C:/Users/LENOVO/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/python-uds-analyzer
```

If the validator cannot run because `yaml` is missing, report that blocker instead of silently skipping validation.

# Git, generated-data, and repository hygiene rules

## Git And Data Hygiene

### Commit These When Intentional

- source files in `core/`, `gui/`, `config/`, and root Python files
- `README.md`, `requirements.txt`, and other project docs
- `AGENTS.md`
- `.cursor/rules/`
- `.codex/skills/`
- `ai-rules/`
- project input config such as `config/ecu_config.xlsx`

### Do Not Commit These

- `.venv/`
- `__pycache__/`
- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
- `logs/`
- `output/`
- generated Excel reports
- converted logs
- temporary cache/build/dist folders

### Git Workflow

When asked to link, commit, or push:

1. Check whether Git is installed.
2. Check whether `.git` exists.
3. Preserve or create `.gitignore`.
4. Initialize only if `.git` is absent.
5. Set or verify `origin`.
6. Stage intended files only.
7. Commit with a concise message.
8. Push only when authentication and remote access are available.

If Git, GitHub auth, or the remote repository is unavailable, stop after preparing local files and report the exact blocker.

