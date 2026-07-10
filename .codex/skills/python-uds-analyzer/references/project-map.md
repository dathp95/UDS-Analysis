# Project Map

Python UDS Analyzer is a PySide6 desktop app for parsing vehicle diagnostic logs and producing transaction reports.

## Runtime Flow

1. `main.py` creates `QApplication` and opens `gui.windows.main_window.MainWindow`.
2. `MainWindow` collects the log file path, runs `MainController.fn_analyze_log`, displays rows through the presenter/table, and exports through `ExportController`.
3. `core.pipeline.run_pipeline` loads the log, loads ECU mapping, parses UDS payloads, builds transactions, builds ECU reports, and returns summary/report/transaction data.
4. `core.report_export.export_workbook` writes Excel output with one `Summary` sheet and one sheet per ECU.

## Important Data Contracts

Parsed messages:

- `timestamp`
- `can_id`
- `dlc`
- `data`

Completed payloads and requests/responses:

- `timestamp`
- `can_id`
- `payload`

Transactions:

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

Activity table columns:

- `No`
- `Time(s)`
- `Service`
- `Activity`
- `Request`
- `Response`
- `RT(ms)`
- `Status`
- `Pending`

## Git Hygiene

Commit source, config, agent rules, skills, and intentional project assets.

Do not commit:

- `.venv/`
- `__pycache__/`
- `logs/`
- `output/`
- temporary cache/build folders

`config/ecu_config.xlsx` is a project input workbook and can be committed when the user wants the app to be reproducible from the repository.
