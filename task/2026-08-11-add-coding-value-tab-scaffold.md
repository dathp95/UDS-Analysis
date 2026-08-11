# Add Coding Value Tab Scaffold

## Request
Them mot tab moi ben canh tab Log Analyzer ten la `Coding value`. Hien tai chi can panel rong va chia structure de sau nay user nhap/giai ma dai coding value.

## Change
- Them `gui/tabs/coding_value_tab.py`.
- Them package `gui/widgets/coding_value/`.
- Them `CodingValuePanel` la panel rong co title `Coding Value`, dung groupbox style hien co.
- Cap nhat `gui/windows/main_window.py` de thu tu tab la:
  - `Log Analyzer`
  - `Coding value`
  - `Vehicle Manager`
- Cap nhat theme refresh cho tab moi.
- Them regression test trong `tests/gui/test_main_window_shortcuts.py`.

## Verification
- Passed: `python -m unittest tests.gui.test_main_window_shortcuts`
- Passed: `python -m unittest tests.gui.test_main_window_shortcuts tests.gui.test_filter_box_payload_editing tests.gui.test_quick_access_export tests.gui.test_result_table_quick_filter`
- Passed: `python -m py_compile gui/windows/main_window.py gui/tabs/coding_value_tab.py gui/widgets/coding_value/coding_value_panel.py tests/gui/test_main_window_shortcuts.py`
- Full `python -m unittest discover` still fails because local dependencies `cryptography` and `can` are missing.
