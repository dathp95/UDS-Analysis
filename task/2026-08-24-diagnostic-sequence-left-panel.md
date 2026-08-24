# Diagnostic Sequence Left Panel

## Summary

- Added reusable `DiagnosticSequenceList` widget under `gui/widgets/diagnostic/`.
- The widget uses `DiagnosticSequenceRepository`; it does not parse/read JSON directly.
- Added left panel to `CANInterfaceTab` below the CAN config/action row.
- Added scrollable sequence list with checkboxes, `Select All`, empty state, and invalid-file error display.
- Added separate active-click behavior via `sequence_selected` while checkbox state remains future execution selection state.
- Added public APIs:
  - `fn_refresh_sequences()`
  - `fn_selected_sequences()`
  - `fn_clear_selection()`
- Added signals:
  - `sequence_selected`
  - `selection_changed`

## Behavior Covered

- Valid sequence files are displayed with numeric prefix and JSON sequence name.
- Sequence ordering uses numeric filename prefix when present.
- `Select All` checks/unchecks all valid sequences.
- Manual item checkbox changes update `Select All` without recursive signal loops.
- Refresh preserves selected sequences by path when possible.
- Invalid JSON is skipped safely and shown in the error label.
- Empty folder shows `No diagnostic sequences found.`

## Verification

- `python -m py_compile gui\widgets\diagnostic\diagnostic_sequence_list.py gui\tabs\can_interface_tab.py tests\gui\test_diagnostic_sequence_list.py tests\gui\test_can_interface_tab.py`
- `python -m unittest tests.gui.test_diagnostic_sequence_list tests.gui.test_can_interface_tab tests.repositories.test_diagnostic_sequence_repository`
- MainWindow offscreen smoke test: CAN Interface left panel loaded the sample diagnostic sequence.

## Scope Notes

- No sequence execution was implemented.
- No CAN, ISO-TP, UDS runtime, RUN, STOP, Report, or center table editing was added.
