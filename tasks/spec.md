# Spec: Log Analyzer selection safeguards

## Objective
Make selecting a diagnostic log safer in Log Analyzer. The Vehicle field starts empty, Analyze explains when no vehicle has been chosen, and logs containing multiple `PT BO INFO` markers are rejected before analysis.

## Commands
- Focused test: `python -m unittest tests.core.test_log_validation`
- Full test suite: `python -m unittest discover`
- Syntax check: `python -m py_compile core/log_validation.py gui/tabs/log_analyzer_tab.py gui/widgets/vehicle_manager/vehicle_selector.py`

## Project Structure
- `core/log_validation.py`: log-content validation.
- `gui/tabs/log_analyzer_tab.py`: UI state and user-facing warning.
- `gui/widgets/vehicle_manager/vehicle_selector.py`: optional empty selection for consumers that need it.
- `tests/core/test_log_validation.py`: validation regression tests.

## Code Style
Use small named functions, validate external file contents at the UI boundary, and keep Vehicle Manager's existing selection behavior unchanged.

## Testing Strategy
Use `unittest` with temporary files for marker validation. Perform a PySide runtime smoke check for the initial empty Vehicle state.

## Boundaries
- Always: preserve existing Vehicle Manager behavior and validate selected files before analysis.
- Ask first: change supported file formats or vehicle configuration data.
- Never: modify existing vehicle configuration data for this feature.

## Success Criteria
- Log Analyzer starts with no selected vehicle.
- Selecting only a log still permits Analyze, which reports that a vehicle is required.
- A file with two or more `PT BO INFO` markers is cleared and rejected with a warning.
- A file with zero or one marker remains selectable.

## Open Questions
- The detector uses literal `PT BO INFO` markers in the selected file. This is the observable format currently available in the app.
