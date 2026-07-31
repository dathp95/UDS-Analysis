# Implementation Plan: Log Analyzer selection safeguards

## Overview
Add a focused core validator, then connect it to the Log Analyzer selection and action state without changing the Vehicle Manager workflow.

## Architecture Decisions
- Keep marker detection in `core` so it is independent of Qt and testable with temporary files.
- Add an opt-in empty state to `VehicleSelectorWidget`; only Log Analyzer opts in.
- Keep the existing `AnalysisController` validation as the final guard for missing Vehicle.

## Task List

### Phase 1: Reject unsuitable logs
- [x] Add test coverage and a streaming marker-count helper.
- [x] Reject a selected file when it contains two or more markers.

### Phase 2: Selection experience
- [x] Allow Log Analyzer, but not Vehicle Manager, to have an empty Vehicle selection.
- [x] Enable Analyze after a valid log is chosen so the existing missing-Vehicle warning can be shown.

### Checkpoint: Complete
- [x] Focused and full tests pass.
- [x] PySide smoke check confirms Log Analyzer starts with an empty Vehicle field.

## Risks and Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Large text logs | Slow UI | Scan in fixed-size blocks and stop once the second marker is found. |
| Shared selector behavior | Vehicle Manager regression | Make empty selection opt-in. |

## Open Questions
- None.
