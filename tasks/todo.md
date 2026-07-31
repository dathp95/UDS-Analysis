## Task 1: Validate unsuitable logs (Complete)

**Acceptance criteria:**
- [x] Files with two `PT BO INFO` markers are identified.
- [x] Files with zero or one marker are accepted.

**Verification:**
- [x] `python -m unittest tests.core.test_log_validation`

**Dependencies:** None

**Files likely touched:**
- `core/log_validation.py`
- `tests/core/test_log_validation.py`

**Estimated scope:** Small

## Task 2: Apply validation to Log Analyzer (Complete)

**Acceptance criteria:**
- [x] Log Analyzer starts with no selected Vehicle.
- [x] Analyze can surface the existing Vehicle-required message after selecting a valid log.
- [x] Invalid log paths are cleared and warned about.

**Verification:**
- [x] `python -m unittest discover`
- [x] PySide runtime smoke check.

**Dependencies:** Task 1

**Files likely touched:**
- `gui/tabs/log_analyzer_tab.py`
- `gui/widgets/vehicle_manager/vehicle_selector.py`

**Estimated scope:** Small
