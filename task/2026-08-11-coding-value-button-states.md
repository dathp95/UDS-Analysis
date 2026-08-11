# Coding Value button states

## Yeu cau
Sau khi import Coding Value nhung chua co payload de encode, cac nut thao tac nhu CHECK, Copy, Clear, Export can disabled va CHECK khong duoc tu tao cot before/result.

## Thay doi
- Them trang thai _has_encoded_payload trong CodingValuePanel.
- Dong bo enabled/disabled cho Encode, Copy, Clear, Refresh, preview actions va table actions bang _update_action_states().
- Guard check_coding_value() de no-op khi chua co payload/baseline hop le.
- Them regression test cho case import khi payload rong, sau do encode va clear.

## Verification
- python -m unittest tests.gui.test_coding_value_tab.CodingValueTabTests.test_action_buttons_require_payload_data_after_import
- python -m unittest tests.gui.test_coding_value_tab
- python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts
- python -m py_compile gui/widgets/coding_value/coding_value_panel.py tests/gui/test_coding_value_tab.py