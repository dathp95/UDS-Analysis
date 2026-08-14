# Log Analyzer Quick Filter Bottom Actions

Date: 2026-08-14

## Request
Improve the Log Analyzer left panel so the bottom area contains only three buttons: Add, Import, Export, while the remaining area belongs to Quick Filter.

## Changes
- Updated `LeftPanel` so `QuickAccessWidget` fills the whole left panel with stretch factor 1.
- Removed the extra outer stretch that previously left blank space below Quick Filter.
- Kept QuickAccessWidget structure as scroll area + bottom action row.
- Stored the bottom action row as `self.action_layout` for layout verification.
- Added tests confirming:
  - Quick filter scroll area receives remaining space.
  - Bottom action row contains Add, Import, Export in order.
  - LeftPanel gives all remaining area to QuickAccessWidget.

## Verification
- `python -m unittest tests.gui.test_quick_access_export` passed.
- `python -m py_compile gui\\widgets\\log_analyzer\\quick_access.py gui\\widgets\\log_analyzer\\left_panel.py tests\\gui\\test_quick_access_export.py` passed.
