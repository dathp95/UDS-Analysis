# Clear Quick Filter Table Selection

## Request
Khi user doi quick filter trong tab Analyze Log, table khong duoc giu row selection cu. Sau moi lan chon filter, table can o trang thai chua chon row nao.

## Change
- Cap nhat `gui/widgets/log_analyzer/result_table.py`.
- Sau khi `fn_apply_quick_filter()` an/hien row va cap nhat mau row xong, table goi:
  - `clearSelection()`
  - `setCurrentCell(-1, -1)`

## Reason
`QTableWidget` giu selection/current index theo row trong model. Khi filter chi hide/show row, selection cu van ton tai va hien lai khi row do duoc show lai.

## Verification
- Added regression test: `tests/gui/test_result_table_quick_filter.py`.
- Passed: `python -m unittest tests.gui.test_result_table_quick_filter`
- Passed: `python -m unittest tests.gui.test_result_table_quick_filter tests.gui.test_quick_access_export tests.gui.test_main_window_shortcuts`
- Passed: `python -m py_compile gui/widgets/log_analyzer/result_table.py tests/gui/test_result_table_quick_filter.py`
- Full `python -m unittest discover` still fails because local dependencies `cryptography` and `can` are missing, not because of this quick filter change.
