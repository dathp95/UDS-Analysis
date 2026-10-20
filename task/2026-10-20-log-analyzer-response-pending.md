# Log Analyzer: bounded Response Pending matching

## Real log evidence

Source: `logs/wild.asc`, read only, 104676593 bytes.
SHA-256 before/after inspection:
`1ba02ac32867206289014b8f889c1668a141588f7dfa9b82a75addd00ae8b14d`.

No valid `7F 31 78` or terminal `7F 31 XX` sequence was found.
The requested RoutineControl failure therefore cannot be confirmed from this
file. Raw payload prefixes resembling `31`/`71` occur on background CAN IDs;
they are not sufficient evidence of diagnostic RoutineControl transactions.

The existing ASC reader accepts 1512 classic CAN frames (channels 1/3/4/5:
725/435/284/68). The file also contains 571125 CANFD records (channels 1/3/4:
196269/172455/202401), which its current classic ASC reader does not accept.
A separate read-only column inspection, followed by per-channel reconstruction,
also found no `7F 31 XX` sequence in these CANFD records. No parser was changed.
That inspection is not a claim of general CANFD/ISO-TP parser validation.

The same pending matching bug IS reproducible on SID `14` (ClearDiagnosticInformation)
on classic CAN channel 5, using the existing WILD ECU mappings:

| Request time (s) | Request CAN ID | Response CAN ID | Request | Pending count | Final time (s) | Final payload | Total RT (s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 21.903148 | 686 | 606 | 14 FF FF FF | 6 | 30.936407 | 54 | 9.033259 |
| 31.994685 | 681 | 601 | 14 FF FF FF | 8 | 43.116299 | 7F 14 72 | 11.121614 |
| 48.251973 | 681 | 601 | 14 FF FF FF | 8 | 59.375069 | 7F 14 72 | 11.123096 |
| 75.917500 | 681 | 601 | 14 FF FF FF | 8 | 87.040603 | 7F 14 72 | 11.123103 |

All CAN IDs above are hexadecimal. Pending payloads are `7F 14 78`.

Pending timestamps, in seconds:
- Request 21.903148: 21.953792, 23.455717, 24.961432, 26.457965, 27.963830, 29.464922.
- Request 31.994685: 32.048895, 33.549796, 35.051266, 36.562835, 38.058473, 39.560158, 41.061087, 42.562590.
- Request 48.251973: 48.302817, 49.809509, 51.305330, 52.812040, 54.312623, 55.813956, 57.321008, 58.816435.
- Request 75.917500: 75.973422, 77.469800, 78.971343, 80.472150, 81.978397, 83.480064, 84.980937, 86.482399.

New channel-5 requests before each final response are functional TesterPresent
(`3E 80`, CAN ID `6FF`), not competing routine/service requests:
- First: 22.004134, 25.016194, 28.030189.
- Second: 34.055185, 37.067665, 40.078730, 43.091018.
- Third: 49.115665, 52.128276, 55.140849, 58.154398.
- Fourth: 76.231510, 79.243929, 82.256785, 85.269350.

No ambiguous or unmatched responses were found in these four mapped SID-14
transactions. This is not a claim that every frame in the entire capture is
matched. Unmapped/background traffic is not assigned to these transactions.

## Root cause and algorithm

Before: find a positive response using the normal timeout and next-request
boundary, then collect negatives only up to that fixed endpoint. NRC 0x78
does not extend ownership. With no positive, the last negative (including 78)
is displayed. Response time is calculated for positives only. A terminal NRC
can also be incorrectly overridden by a later positive.

HEAD matcher vs modified matcher was compared in memory on all four real
transactions above. For each of the three 11-second transactions, HEAD returns
`7F 14 78` and only 7 pending responses; the new matcher returns `7F 14 72`,
all 8 pending responses, and the final response time. ISO-TP reconstruction
and the channel-5 parser are not the cause of these reproduced cases.

After: sort positive/negative events per mapped response CAN ID, start within
the normal deadline, and extend the deadline only after a matching `7F SID 78`.
Check positive SID and existing identifier rule (RoutineControl now checks
subfunction plus both Routine ID bytes). Stop at the first genuine terminal
response; consume each associated response once. Compute RT from request to
that terminal response, whether positive or negative.

A non-TesterPresent request on the same request CAN ID ends ownership, with
an exclusive boundary (equal timestamps are not assigned to the older request).
Requests to another ECU and TesterPresent keepalives do not interrupt pending.
An interrupted pending transaction becomes `PENDING_AMBIGUOUS`; same-SID retries
within its remaining bound are also conservatively marked ambiguous. Their
responses stay unassigned rather than being falsely attributed. This includes
different-RID retries: negatives carry SID but no RID. Pending count/details
include only reliably associated messages before the competing request.

## Configuration and display

`config/uds_services.json`, seconds:
- `timeout.positive_response`: unchanged at 10.0.
- `timeout.response_pending`: defaults to 120.0, including when absent in older configs.

`response_pending` is a total request-to-final bound, NOT a per-NRC restarted
timer or a negotiated P2-star timeout. Effective extended limit is
`max(positive_response, response_pending)`. Repeated pending cannot extend it
indefinitely. Non-finite, zero, and negative limits are rejected. Existing
`build_transactions_v4` calls remain valid; tests/callers may override the
extended bound with keyword-only `pending_timeout`. Configuration reload is
read through `uds_lookup`, so pipeline signatures remain unchanged.

Positive payload takes display priority; otherwise only terminal negatives
are eligible. Pending-only results have empty final payload/RT and status
`PENDING_TIMEOUT` (also used if the capture ends without a final response).
Pending details remain in `negative_responses` and `response_pending_count`.

ResultTable and transaction formatter already pass status text through without
an enum whitelist. Search can find the new status. Quick Filter matches only
the displayed final payload: pending-only cannot match a response filter of
`7F SID 78`. Request-only filtering still works. No GUI implementation changed.

Summary includes pending timeout/ambiguity in the existing timeout total, with
separate appended `pending_timeout`/`pending_ambiguous` counters. Existing column
positions are preserved. Excel uses the same final-payload selection in ALL_ECUS
and ECU sheets; ECU sheets retain their separate Pending count column.

## Verification

- RED: new 16-test pending suite reproduced 12 failures and 1 missing-API error.
- GREEN: focused matcher/formatter suite initially passed 26/26.
- Added guards for TesterPresent, timeout boundaries/invalid values, config
  default/reload, real SID-14 timings, and actual offscreen Qt filtering.
- Broader regression: 129 tests, 128 passed, 1 pre-existing failure in
  `tests.core.test_report_export.ReportExportTests.test_export_workbook_applies_shared_table_style_to_all_sheets`.
  It expects Summary A2 to contain BCM, but the existing banner places the
  header `ecu` there. Reproduced with HEAD export source loaded in memory.
- Final rerun excluding that independently confirmed baseline test: 128/128
  passed. `py_compile` passed for all 8 edited/new Python files, and
  `git diff --check` reported no whitespace errors. Final SHA-256 still matches.
- Real temporary BLF, converted ASC, and DSA-TXT files run through the pipeline;
  workbook contents and offscreen ResultTable/Quick Filter behavior are tested.
- No physical ECU/hardware run or interactive desktop visual validation.

## Files changed

- `core/build_transactions.py`
- `core/config_loader.py`
- `core/uds_lookup.py`
- `core/report_engine.py`
- `config/uds_services.json`
- `tests/core/test_response_pending.py` (new)
- `tests/core/test_transaction_formatter.py`
- `tests/core/test_uds_config_loader.py`
- `tests/gui/test_result_table_quick_filter.py`
- `task/2026-10-20-log-analyzer-response-pending.md` (this report)

Existing user changes in `config/quick_filters.json` were preserved. No parser
format, vehicle mapping, licensing, activation, or original log was modified.
No commit was created.

Suggested commit message:
`log analyzer - response pending matching fix commit 6`
