# Output report folders

## Yeu cau
Doi cau truc folder trong `output`: bo 4 folder cu `Reports`, `Logs`, `Temp`, `Cache`; dung `Report_LogAnalyzer` cho export cua tab Log Analyzer va `Report_CodingValue` cho export cua tab Coding Value.

## Thay doi
- Them `LOG_ANALYZER_REPORT_DIR = OUTPUT_DIR / "Report_LogAnalyzer"`.
- Them `CODING_VALUE_REPORT_DIR = OUTPUT_DIR / "Report_CodingValue"`.
- Startup chi tao `output`, `Report_LogAnalyzer`, `Report_CodingValue`.
- Log Analyzer export sang `output/Report_LogAnalyzer/<date>`.
- Coding Value export sang `output/Report_CodingValue/<date>`.
- Build release chi tao 2 report folder moi.
- Migrate du lieu cu trong `output/Reports` sang 2 folder moi theo ten file, sau do xoa `Reports`, `Logs`, `Temp`, `Cache`.

## Verification
- `python -m unittest tests.core.test_output_report_paths`
- `python -m py_compile config/paths.py core/services/startup_service.py core/services/report_service.py gui/widgets/coding_value/coding_value_panel.py build_release.py tests/core/test_output_report_paths.py tests/gui/test_coding_value_tab.py`
- `python -m unittest tests.core.test_output_report_paths tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts`