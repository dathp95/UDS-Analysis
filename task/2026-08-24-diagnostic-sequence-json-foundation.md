# Diagnostic Sequence JSON Foundation

## Summary

- Added GUI-independent diagnostic sequence dataclasses:
  - `DiagnosticStep`
  - `DiagnosticTestCase`
- Added `DiagnosticSequenceRepository` for diagnostic sequence storage:
  - List `.json` sequence files.
  - Load and validate one sequence.
  - Convert JSON into `DiagnosticTestCase`.
  - Save/update `DiagnosticTestCase` back to JSON.
  - Fail safely with `DiagnosticSequenceValidationError` for invalid JSON, invalid HEX, and missing required fields.
- Added `DIAGNOSTIC_SEQUENCES_DIR` path under `config/paths.py`.
- Added sample file `config/diagnostic_sequences/0002_READ_VIN.json`.
- Added repository tests for load, save, validation, invalid JSON, and sorted listing.

## Validation Covered

- Required `schema_version`.
- Required non-empty `name`.
- `steps` must be a list.
- Step required fields: `step`, `sequence_name`, `ecu`, `request`.
- `request` and `expected_response` HEX normalization.
- `delay_ms >= 0`.
- `repeat >= 1`.
- `match` must be `prefix`, `exact`, or `wildcard`.

## Verification

- `python -m unittest tests.repositories.test_diagnostic_sequence_repository`
- `python -m py_compile core\diagnostic_sequence.py repositories\diagnostic_sequence_repository.py config\paths.py tests\repositories\test_diagnostic_sequence_repository.py`
- Repository default root successfully loaded `config/diagnostic_sequences/0002_READ_VIN.json`.

## Scope Notes

- No GUI execution was added.
- No CAN, ISO-TP, UDS send/receive, RUN, STOP, or Report logic was added.
