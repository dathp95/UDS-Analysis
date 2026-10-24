# Q Current Commit 41: Large Dataset Loading Review

## Baseline and Findings

Reviewed HEAD `58a99fa` (`q current -commit 41`). No commit or push was made.

- P1: `_current_import_finished()` and `_current_dataset_loaded()` call
  `_load_samples_into_workspace()` on the GUI thread. Its synchronous
  `_populate_review_table()` creates three QTableWidgetItems per sample using
  insertRow/setItem. This prevents progress painting and input dispatch.
- P1: `_initialize_analysis_range_from_samples()` parses every timestamp on the
  GUI thread. Manual-end-mode clamping can repeat the same scan when busy state
  is restored. Selecting review rows also reparses the complete dataset.
- P2: `_refresh_dataset_combo()` calls `list_datasets()` after import. This opens
  SQLite databases and initializes/checks their metadata on the GUI thread.
- P2: inherited `PrimaryTable.fn_refresh_theme()` recolors every table cell.
- Additional GUI work: copying the sample list, resetting the previous table and
  chart, resetting controls, catalog widget updates, header sizing, scroll reset,
  and initial painting. Source path resolution/directory creation/existence
  checks also run synchronously before or during replacement confirmation.
  Confirmation/information dialogs run a nested Qt event loop; they are not the
  CPU-bound freeze described here.

A cProfile run with 50,000 synthetic datetime samples spent 19.386 s in the GUI
workspace callback: 13.328 s in table population and 6.046 s in range
initialization. Profiling adds overhead; use the unprofiled numbers below for
before/after comparisons.

## Fix and Architecture

Preserved `QCurrentTaskRunner`, QThread lifecycle, progress styling, SQLite schema,
normalization, analysis rules, chart rendering and report generation.

Before: worker parses/imports/reads SQLite, then GUI materializes all cells,
calculates the range, and queries the dataset catalog.

After: worker also prepares elapsed timestamps/range bounds and the catalog.
The GUI attaches the complete sample list to a QAbstractTableModel without a
second sample-list copy. QTableView displays an initial batch of 512 rows and
calls `fetchMore()` for later batches. Formatting and row colors are evaluated
on demand. Theme refresh repaints the viewport without traversing all samples.
The fetch protocol follows Qt's
[Fetch More example](https://doc.qt.io/qtforpython-6/examples/example_widgets_itemviews_fetchmore.html).

`IMPORTING` remains active throughout file parsing, SQLite operations, timestamp
preparation and model attachment. `IMPORTED` means the complete dataset and
initial review model are ready; it does not mean every offscreen row has been
eagerly rendered. No synthetic percentages were added.

Copy Data Review reads all samples, including unfetched rows. Export still uses
the full `current_samples` collection. Selection/context-menu row indices remain
source indices. Analysis-range filtering and chart interactions are unchanged.
Commit 41 has no separate Data Review search/filter UI; the new model is tested
with QSortFilterProxyModel without introducing a new filter interface.

## Modified Files and Functions

- `gui/tabs/q_current_tab.py`: `_create_review_table`, signal connection,
  `_begin_operation`, `_confirm_current_import`, `_current_import_finished`,
  `load_selected_dataset`, `_current_dataset_loaded`, `_load_samples_into_workspace`,
  new `_get_elapsed_seconds`, range initialization/clamping, review row navigation,
  `_build_chart_data`, clear, `_populate_review_table`, `_review_table_to_text`,
  and `_refresh_dataset_combo`.
- `core/q_current_loading.py`: moved the unchanged elapsed-time calculation into
  Qt-free code; added prepared workspace data and stage timing helper.
- `gui/widgets/q_current/review_table.py`: lazy model and themed QTableView.
- `tests/gui/test_q_current_tab.py`: equivalent assertions/signals using model/view APIs.
- `tests/gui/test_q_current_review_model.py`: incremental rows, formatting,
  selection, proxy filtering and themes.
- `tests/gui/test_q_current_large_loading.py`: repeated 50,000-sample SQLite loads,
  GUI heartbeat, worker affinity, status lifecycle, complete copy and analysis.
- `tests/core/test_q_current_loading.py`: timestamp/range equivalence and timing errors.
- `tests/performance/benchmark_q_current_loading.py`: reproducible benchmark.
- This report.

`gui/workers/q_current_worker.py` and `analysis_progress.py` were inspected and
left unchanged. No unrelated tabs, licensing code, input logs, user databases
or database schemas were modified.

## Measurements

Synthetic CSV with Trigger time/No1 Average Ch1, 1 ms datetime samples, fresh
workspace-local SQLite databases; Qt offscreen on this machine. Same benchmark
function before and after, two baseline repetitions and two final confirmation
repetitions for 50,000 rows. Values are observed ranges, not guarantees.

| Stage, 50,000 samples | Commit 41 | Fixed |
| --- | --- | --- |
| File parse/normalization, worker | 10.546-11.588 s | 12.715-13.116 s |
| SQLite write/import, worker | 0.329-0.340 s | 0.423-0.452 s |
| SQLite sample read, worker | 0.422-0.481 s | 0.584-0.740 s |
| Table initialization | 5.019-5.065 s, all cells | 0.136-0.177 ms, lazy model bind |
| Analysis-range GUI initialization | 0.996-1.069 s | 0.284-0.522 ms |
| Complete GUI workspace callback | 6.078-6.100 s | 13.840-40.325 ms |
| Largest import heartbeat gap | 6.118-6.124 s | 0.130-0.273 s |
| Whole-tab theme refresh | 0.617-0.989 s | 0.263-0.347 s |
| Import through initial UI readiness | 17.485-18.600 s | 16.722-16.996 s |

With 1,000 samples, baseline table creation took 102.6-122.3 ms; model binding
took 0.135-0.158 ms. Both variants passed exactly the requested sample count
to the workspace: 1,000 and 50,000 respectively.

The table figure measures the named binding method, not deferred painting or
materializing all offscreen rows. The workspace and heartbeat figures separately
cover event-loop responsiveness. This is a responsiveness fix, not a claim that
parsing or SQLite became faster. Those algorithms are unchanged and their
measured durations varied with host load. Extra exploratory runs observed GUI
heartbeat gaps as high as 1.478 s under load; final confirmation runs were
0.130-0.273 s. No hard real-time responsiveness guarantee is claimed.

Runtime stage measurements are available in `tab.last_loading_timings`, including
`file_parse_s`, `sqlite_write_s`, `sqlite_read_s`, `prepare_s`, `catalog_s`,
`table_bind_s` and `workspace_gui_s` when applicable.

Reproduce: `python -m tests.performance.benchmark_q_current_loading`.

## Validation

- 132 targeted Q Current GUI/core/report and worker tests executed: 128 passed.
- All nine newly added regression tests passed, as did all eight existing
  progress/worker workflow tests (CSV/XLSX, repeat RUN, cancellation and themes).
- The four remaining failures were independently reproduced using HEAD source
  and HEAD tests loaded in memory, without changing working files:
  - old settings-layout rowCount assertion against QHBoxLayout;
  - old default dataset selection expectation;
  - old duration string formatting expectation;
  - old Excel creator metadata expectation.
- Python compileall and git diff whitespace validation passed.
- No native desktop interaction was performed; runtime tests used Qt offscreen.

## Remaining Limits

- SQLite still loads the complete raw dataset into memory; elapsed timestamps
  also occupy memory. This is view virtualization, not database paging.
- File parsing and Python/SQLite loading remain CPU/I/O work in the existing
  thread architecture; the GIL and host load can still introduce short stalls.
- Copying or exporting a very large dataset is still a separate O(N) operation;
  those command implementations were not made asynchronous in this change.
- Initial application/catalog-popup scans and small path metadata operations
  remain synchronous. Very large catalogs or slow/network filesystems warrant
  separate optimization.
- Direct internal calls to `_load_samples_into_workspace(raw_samples)` still
  prepare raw samples synchronously for compatibility. Actual import/load paths
  always supply worker-prepared data.
