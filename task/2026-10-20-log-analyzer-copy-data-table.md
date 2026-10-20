# Log Analyzer: Copy Data Table

## Changes

- Renamed the existing button to `COPY DATA TABLE`; kept `copy_clicked`.
- Replaced log-file clipboard access with ResultTable's non-hidden row snapshot.
  Rows outside the viewport are included unless explicitly hidden by filtering.
  Selection is ignored and current row order is preserved. Existing Search,
  Quick Filter and ECU-filter behavior is not changed or independently reapplied.
- Shared `TRANSACTION_COLUMNS` and `fn_build_transaction_rows` define the existing
  ALL_ECUS schema: ECU, Time, Activity, Request, Response, RT (ms), Status.
  ResultTable uses that same schema for headers and cell population; Copy uses
  its already formatted displayed values. Excel export implementation is unchanged.
- TSV has one header row, tab delimiters and CRLF row endings, using Python's
  `csv` excel-tab dialect for quote escaping. Embedded CR/LF/tab characters are
  replaced with spaces. None/missing/blank cells remain blank; zero is preserved.
  Payloads are not shortened. Excel's normal numeric parsing can display 100.0
  as 100, exactly as an exported General-format numeric cell; numeric values
  and the existing response-time rounding are unchanged.
- Success reports the copied transaction count. No visible rows produces a
  short information message and leaves the clipboard unchanged. Clipboard errors
  produce a warning rather than success. Empty analysis keeps Copy disabled.
- Context-menu Copy Request/Response/Transaction methods are unchanged.
- No original ASC/BLF/TXT file, export service, parser or licensing file changed.
  No commit was created.

## Verification

- RED: new tests reproduced the old button label and missing visible-row copy API.
- 12 new tests pass, including all rows vs a real generated ALL_ECUS worksheet,
  Quick Filter, Search, ECU filter, hidden selection, reordered rows, long payload,
  blank Response/RT, zero/None/missing cells, quotes/Unicode/control characters,
  empty table/filter results, button signal/lifecycle and clipboard error handling.
- Light/Dark clipboard contents match; actual offscreen Qt button rendering and
  label width are checked in both themes.
- Focused Copy/formatter/context-menu run: 28/28 passed.
- Wider regression: 88 tests, 84 passed, 4 existing failures. Three are detail-panel
  tests expecting single newlines where the baseline uses double newlines; one
  Excel test expects BCM at Summary A2, which is the existing `ecu` header after
  the banner. All four were reproduced with HEAD sources loaded in memory.
- Final run excluding those four confirmed baseline cases: 84/84 passed.
  Syntax compilation of all six Python files and `git diff --check` passed.
- Desktop Excel paste was NOT verified. The Windows Computer Use helper failed
  initialization twice (`helper_unknown_error: setup refresh had errors`). Actual
  Qt clipboard text, TSV parsing and exported workbook values were checked instead.
  Excel's live clipboard parser remains the manual verification gap.

## Files

- `core/transaction_formatter.py`
- `gui/controllers/clipboard_controller.py`
- `gui/tabs/log_analyzer_tab.py`
- `gui/widgets/log_analyzer/action_panel.py`
- `gui/widgets/log_analyzer/result_table.py`
- `tests/gui/test_copy_data_table.py` (new)
- `task/2026-10-20-log-analyzer-copy-data-table.md` (this report)
