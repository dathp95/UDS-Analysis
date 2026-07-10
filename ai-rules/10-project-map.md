---
description: Repository structure and ownership map for Python UDS Analyzer
alwaysApply: true
fileMatching: "**/*.py"
---

# Project Map

## Application Shape

- `main.py` starts the PySide6 application.
- `core/` owns parsing, UDS lookup, transaction building, report generation, Excel export, and the analysis pipeline.
- `gui/` owns windows, widgets, controllers, presenters, and styling.
- `config/` owns settings, path constants, UDS config, and the ECU mapping workbook.
- `logs/` and `output/` are local runtime or generated data.
- `.codex/skills/python-uds-analyzer/` contains the project skill for agent workflow.
- `ai-rules/` contains the source rules used to maintain agent-facing rule files.

## First Files To Read

For runtime tasks, inspect the smallest relevant set before editing:

- Entry point: `main.py`
- Pipeline: `core/pipeline.py`
- Parsing: `core/asc_reader.py`, `core/convert_blf.py`
- Transactions: `core/build_transactions.py`, `core/uds_lookup.py`, `core/ecu_mapping.py`
- Reports/export: `core/report_engine.py`, `core/report_export.py`, `core/export_transactions.py`
- GUI flow: `gui/windows/main_window.py`, `gui/controllers/`, `gui/presenters/`, `gui/widgets/`
- Config: `config/paths.py`, `config/settings.json`, `config/uds_config.json`, `config/ecu_config.xlsx`

## Data Contracts

Parsed messages use:

- `timestamp`
- `can_id`
- `dlc`
- `data`

Completed payloads and request/response records use:

- `timestamp`
- `can_id`
- `payload`

Transactions use:

- `ecu`
- `service_id`
- `service_name`
- `display_name`
- `identifier`
- `identifier_name`
- `sub_function`
- `routine_id`
- `routine_name`
- `request`
- `negative_responses`
- `positive_response`
- `response_pending_count`
- `response_time`
- `status`

Activity table columns use:

- `No`
- `Time(s)`
- `Service`
- `Activity`
- `Request`
- `Response`
- `RT(ms)`
- `Status`
- `Pending`

