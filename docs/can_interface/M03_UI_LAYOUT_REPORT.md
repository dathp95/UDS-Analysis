# CAN Interface M03 — Diagnostic Workspace UI ONLY

Ngày xác minh: 2026-10-25. Baseline: commit 55,
`f5226fb5218d01510f454ef2dd7c8cc00015e0a7`.
Triển khai theo `.codex/skills/can-m03-ui-layout/SKILL.md`; không commit/push.

## Phạm vi và tài liệu tham chiếu

Đã kiểm tra CAN Interface/M01/M02, VehicleService/models/repository/selector,
Diagnostic Sequence model/repository/widgets, Save Order của Coding Value,
Log Analyzer layout/sidebar, ThemeManager, shared controls và scrollbar styles.
Không sửa backend CAN, state machine hoặc worker M01/M02.

Không tìm thấy ảnh tham chiếu trong workspace hoặc ảnh đính kèm ở lượt yêu cầu
này. Bố cục chi tiết trong skill là nguồn thiết kế thay thế; không tuyên bố đã
so sánh pixel với ảnh gốc. Bốn `.diag` gốc cũng không có; dùng bốn fixture tổng
hợp theo schema được cung cấp, không phải cấu hình ECU/xe thật.

## Kiến trúc trước/sau

Trước:

```text
CANInterfaceTab
  ├─ connection controls + M02 handlers + worker wiring
  ├─ DiagnosticSequenceList
  └─ DiagnosticSequenceTable
```

Sau:

```text
CANInterfaceTab (composition, high-level events, theme)
  ├─ main_splitter [horizontal]
  │   ├─ CanSequenceSidebar
  │   └─ right_splitter [vertical]
  │       ├─ CanDiagnosticTablePanel : DiagnosticSequenceTable
  │       └─ bottom_splitter [horizontal]
  │           ├─ CanSessionPanel
  │           │   ├─ CanConnectionPanel (presentation only)
  │           │   └─ CurrentTestCasePanel (read-only)
  │           └─ CanMonitorPanel (view shell only)
  ├─ CanConnectionController → existing CANService + existing tasks
  └─ CanWorkspaceController → sequence repository + UI preference store

CanSequenceRepository → native DiagnosticSequenceRepository (.json)
                      → import_diag (.diag, data only)
VehicleService → Vehicle.ecus → table ECU options
```

Tab giữ một CANService duy nhất. Connection controller chuyển các handler M02 ra
khỏi tab, giữ nguyên worker ownership, aboutToQuit, cleanup/recovery, guards và
signal flow. Child widget không gọi `fn_connect`, send, receive hoặc raw bus.
Các alias action/control của CAN tab được giữ cho caller/test hiện có.

## File thay đổi và trách nhiệm

| File | Vai trò |
|---|---|
| `gui/tabs/can_interface_tab.py` | Orchestrator, splitters, Vehicle Manager event hookup, theme |
| `gui/controllers/can_connection_controller.py` | Handler/control binding được tách từ tab M02 |
| `gui/controllers/can_workspace_controller.py` | Open/Save As, unsaved switch guard, UI preferences |
| `gui/widgets/can_interface/__init__.py` | Feature package |
| `gui/widgets/can_interface/sequence_sidebar.py` | Search, checkbox/preview, native drag/drop, Save Order |
| `gui/widgets/can_interface/diagnostic_table_panel.py` | View kế thừa native table, exact columns, stable row IDs, runtime display API |
| `gui/widgets/can_interface/connection_panel.py` | Presentation của controls Vector hiện có |
| `gui/widgets/can_interface/current_test_case_panel.py` | Details chỉ đọc, text selectable và tooltip |
| `gui/widgets/can_interface/session_panel.py` | Hai subsection Connection / Current Test Case |
| `gui/widgets/can_interface/can_monitor_panel.py` | Monitor shell, filter và bounded display contract |
| `gui/widgets/can_interface/panel_theme.py` | Container QSS theo object name, không đổi global theme |
| `core/diagnostic_sequence_import.py` | Strict `.diag` → existing model, không Qt/execution |
| `core/can_interface_view.py` | Immutable classic CAN frame presentation model |
| `repositories/can_sequence_repository.py` | Read `.json`/`.diag`, write native `.json` only |
| `repositories/can_interface_ui_store.py` | Atomic display-only preferences |
| `tests/core/test_diagnostic_sequence_import.py` | Schema/type/HEX/source preservation tests |
| `tests/gui/test_can_interface_layout.py` | Splitters, resize, single service owner |
| `tests/gui/test_can_sequence_sidebar.py` | Search, visible selection, real pointer clicks, native row move, Save Order |
| `tests/gui/test_can_diagnostic_table_panel.py` | Columns, row IDs, validation, native Save, runtime/theme |
| `tests/gui/test_can_workspace_controller.py` | Save As, cancel switch, restore, inventory, atomic preference failure |
| `tests/gui/test_can_session_panel.py` | Current row details and Vehicle Manager change event |
| `tests/gui/test_can_monitor_panel.py` | Empty shell, bounded data/filter/counters |
| `tests/gui/render_can_interface.py` | Repeatable offscreen visual QA, synthetic definitions only |
| `tests/gui/test_can_interface_tab.py` | Warning patch target follows new controller location |
| `tests/gui/test_can_connection_tab.py` | Warning patch target follows new controller location |
| `tests/gui/test_main_window_shortcuts.py` | CAN-specific startup test uses real dependencies and no fake channel |
| `tests/fixtures/can_interface/0001.READ&CDS(1).diag` | Synthetic nullable-schema fixture |
| `tests/fixtures/can_interface/0002.READ VIN(1).diag` | Synthetic 16-step VIN definition |
| `tests/fixtures/can_interface/204.BCM&CDS&1.diag` | Synthetic nullable-schema fixture |
| `tests/fixtures/can_interface/9302.MHU&WriteVIN&1.diag` | Synthetic schema fixture; no write execution |
| `docs/can_interface/M03_UI_LAYOUT_REPORT.md` | Báo cáo này |

Tổng cộng 31 file; thư mục skill M03 đã untracked trước khi làm việc và không được
sửa. Không sửa tab khác, shared controls, licensing, config/vehicle dữ liệu thật,
native sequence widgets/repository hay dependency pins.

## Bố cục và visual QA

Initial ratios: sidebar/right 21:79; table/bottom 65:35; connection/monitor 45:55.
QSplitter không collapsible, có stretch factors; không hard-code minimum window
size. Sidebar có minimum 180 px; wide diagnostic table được cuộn ngang, cột resize
được, sorting tắt. Row height kế thừa 34 px; `>` dùng ActionButton 32×28 cục bộ.

| Logical size | Sidebar / Right | Table / Bottom | Session / Monitor |
|---|---|---|---|
| 1600×900 | 324 / 1256 | 572 / 308 | 563 / 689 |
| 1366×768 | 276 / 1070 | 486 / 262 | 480 / 586 |

Đã render Light/Dark ở cả hai kích thước và Qt scale 100%/150%, xem ảnh thực tế
bằng image viewer. 150% giữ hình học logical tương ứng. Font Segoe UI/Consolas được
nạp trực tiếp cho QA vì offscreen font enumeration ban đầu rỗng; không thay font
hoặc dependency của application. Đã dispatch DeferredDelete để không chụp orphan
widgets tạm thời trong test harness. Dark Disconnected status dùng text token dễ
đọc; sidebar không lặp numeric filename prefix.

Ảnh QA nằm trong `output/qa_can_m03/` (gitignored), ví dụ:

- `light_1600x900_100.png`
- `dark_1366x768_100.png`
- `dark_1366x768_150.png`

Lệnh tái tạo: `python -m tests.gui.render_can_interface` và
`python -m tests.gui.render_can_interface --scale 1.5`.
Đây là render Qt offscreen, không phải kiểm thử manual bằng hardware/desktop thật.

## Sequence sidebar, Save và Save Order

- Numeric ordering ban đầu tái sử dụng native sequence list. Search substring
  không phân biệt hoa thường, chỉ hide item, không đổi physical/saved order.
- Click tên hoặc Enter mở preview; click checkbox chỉ chọn batch. Select All/
  clear áp dụng **visible items**, giữ nguyên checkbox của item đang bị ẩn.
- Native InternalMove có insertion indicator. Search khác rỗng vô hiệu hóa drag
  và drop. Thứ tự thay đổi làm `Save Order *` enabled; kéo về baseline thì disabled.
- Chỉ Save Order lưu visual order. Sequence Save, vehicle preference, active
  selection không commit pending reorder. Reload giữ pending order, loại file mất
  và append file mới theo thứ tự xác định.
- Preferences ở `config/can_interface_ui.json`: version, saved order, active
  source, external source inventory và Vehicle **name** theo document. Không lưu
  ECU IDs, DLL, payload hay snapshot sequence trong preferences. Temp file cùng
  directory + replace atomic; lỗi ghi giữ file cũ và xóa temp.
- Mở lại khôi phục order, external sources và last selected sequence. Lựa chọn
  Vehicle được nhớ như view preference vì native sequence schema không có field
  Vehicle association. Splitter positions/column widths chưa persist.

Open file khác khi definition dirty có Save/Discard/Cancel. Save native `.json`
dùng repository hiện có. `.diag` chỉ đọc; Save yêu cầu Save As `.json`. Không cho
ghi `.diag`; destination khác đã tồn tại cần confirm từ Save As dialog. Import
warning nói rõ conversion không lossless cho các field ngoài model native.

## Table, importer và canonical ECU binding

Exact columns:

```text
✓ | Step | ECU | Payload (HEX) | > | Delay (ms) | Repeat |
Expected Response (HEX) | Receive Message (HEX) | Results | Comment
```

Kế thừa native table để giữ HEX/int validation, inherited add values, delete,
reindexing và execution settings. Settings mở controls Loop/Delay/Import hiện có;
không phải transport settings. `sequence_name` cũ vẫn giữ trong model; row mới kế
thừa document title để native Save không thất bại vì field ẩn rỗng. Comment lưu
qua `DiagnosticStep.comment`. Invalid edit revert và hiện notice, không corrupt
definition. Payload/expected/receive có monospace, full tooltip và Ctrl+C trên cell.

Row ID là UUID view-session, không phải captured row index. Add/delete giữ ID của
row còn sống; mỗi lần load document tạo ID mới. Checkbox row tách khỏi row action.
`>` chỉ emit `row_send_requested(step_id)` và hiện notice transport chưa có; **không
gửi UDS**. Run Selected/Stop disabled. Receive/Results khởi tạo `—`, không có fake
Passed/response. Runtime API tách khỏi model và bị reset khi definition thay đổi;
theme refresh giữ semantic outcome colors. Test injected result chỉ kiểm tra view.

`.diag` adapter kiểm tra root/Header/list/item types, ECUName, byte-token HEX,
nonnegative integer Delay, Repeat >=1; bool/float/object sai kiểu bị từ chối.
Map TransMess/ExpectMess/DelayTime/RepeatTimes/Remark vào model hiện có; nullable
ExpectMess/Remark thành rỗng. Tên sequence và step.sequence_name từ filename stem;
match mặc định prefix chỉ là expectation metadata, không thực hiện comparison.
Không dùng Header.IDVehicle để suy Vehicle; không dùng IDReq/IDResp/DLLFile làm
cấu hình canonical; không thực thi TransmitRule/ReceiveRule/unknown keys.
Không có DLL load, eval hoặc shell execution. Label chứa dữ liệu ngoài dùng plain text.

ECU combo chỉ lấy VehicleService.load_vehicle(...).ecus. Không tự chọn Vehicle
đầu tiên; có selector `Select Vehicle`. Chỉ resolve exact name duy nhất; aliases
không được suy đoán. Missing/ambiguous ECU giữ nguyên tên definition, hiện warning
và tooltip. Không có Request ID/Response ID/DLL column/editor. Chọn Vehicle mới
rebind options mà không sửa ECU data hoặc xóa step cũ. Host Vehicle Manager
`vehicle_data_changed` được hook một lần khi tab hiện; có `fn_refresh_vehicles`
cho host khác, không polling.

## Bottom panels và handoff contracts

Connection vẫn dùng snapshot/state/guard M02, một service và bộ task cũ. Current
Test Case chỉ đọc Step i/N, ECU, Payload, Expected, Delay, Repeat; cập nhật khi chọn
row hoặc sửa definition, không có Send button.

Monitor mặc định `Not monitoring`, 0 Frames/Displayed/Dropped. Clear chỉ xóa local
view. CSV và BLF disabled, tooltip nêu chưa triển khai; không tạo file BLF rỗng.
`CanFrameView` là immutable classic CAN presentation data. `append_frame_batch`
chỉ nhận view models trên GUI thread; buffer mặc định tối đa 2000 frames, filter
CAN ID/direction và đếm evicted frames. Không có frame producer/RX consumer. Active
monitor/logging state bị từ chối trong M03.

Handoff cho M04/later runner:

- `sequence_open_requested`, `checked_sequences_changed`, `order_save_requested`.
- `row_selected`, `row_send_requested`, `selected_rows_changed`, `sequence_modified`.
- `set_step_running`, `set_step_result`, `reset_runtime_results` chỉ đổi view.
- `append_frame_batch`, `clear_display`, inactive monitoring/logging setters.
- Future runner cần transport thật, lấy ECU identity từ VehicleService, marshal
  mọi update về GUI, hủy/ignore operation của document cũ khi load/reset IDs.

## Checkpoint và kết quả kiểm thử

| Pha | Kết quả |
|---|---|
| UI-01 Shell + M01/M02 GUI/worker | 35 PASS |
| UI-02 Sidebar + native list + Coding Save Order | 37 PASS |
| UI-03 Table + native table/repository | 63 PASS |
| UI-04 Import/Save As/Vehicle/persistence tập trung | 13 PASS |
| UI-05 Session/monitor + M01/M02 GUI/worker | 37 PASS |
| UI-06 Final CAN M01/M02/M03 + native sequences | **152 PASS, 0 fail/error/skip**, 9.223 s |
| Save Order/theme, Quick Filter logic, DSA Log Analyzer, Vehicle service/repository | **56 PASS**, 7.385 s |
| MainWindow CAN startup smoke | **1 PASS**, 16.946 s |
| compileall + git diff --check | PASS |

RED tests được chạy trước shell/sidebar/table/importer/bottom implementation. Review
còn bắt và bổ sung RED regression cho hidden sequence_name; fix trước final run.
MainWindow CAN test sửa fake `can` quá nông làm mất `can.io` của BLF reader, dùng
dependency thật và kỳ vọng channel chưa discovery là None, không fake channel 0.

Final CAN command: `python -X faulthandler -m unittest` với các module sau:

```text
tests.core.test_diagnostic_sequence_import
tests.gui.test_can_interface_layout
tests.gui.test_can_sequence_sidebar
tests.gui.test_can_diagnostic_table_panel
tests.gui.test_can_workspace_controller
tests.gui.test_can_session_panel
tests.gui.test_can_monitor_panel
tests.services.test_can_service
tests.services.test_vector_discovery
tests.services.test_can_connection
tests.services.test_owned_vector_bus
tests.gui.test_can_interface_tab
tests.gui.test_can_connection_tab
tests.gui.test_can_connection_worker
tests.gui.test_can_discovery_worker
tests.gui.test_diagnostic_sequence_table
tests.gui.test_diagnostic_sequence_list
tests.repositories.test_diagnostic_sequence_repository
```

Lần chạy thực tế dùng unittest loader/TextTestRunner trên các module này, đặt
`tempfile.tempdir` vào TemporaryDirectory trong workspace và root NullHandler
(không disable logging; assertLogs vẫn chạy). GUI offscreen; hardware/transport
được fake/mock như test M01/M02, không cần Vector thật.

### Lỗi baseline ngoài phạm vi — không che hoặc sửa

Hồi quy mở rộng ban đầu: 244 tests, 8 failures ngoài CAN. Đã chạy độc lập bốn module
liên quan, **76 tests / 10 failures / 0 errors**, xác nhận
`gui.tabs.can_interface_tab` **không được import** trong process đó. Source và test
của bốn khu vực dưới không có diff so với commit 55:

| Module | Các failure hiện có |
|---|---|
| `test_ecu_workspace_sidebar` | `test_active_workspace_uses_theme_success_green`; `test_initial_empty_sidebar_has_add_control`; `test_workspace_rows_are_compact_buttons_without_permanent_delete_button` |
| `test_quick_access_reorder` | `test_click_context_menu_and_theme_still_work_after_reorder`; `test_drag_first_last_and_last_first_preserves_selection_without_click_or_save` |
| `test_log_analyzer_working_log` | `test_action_panel_has_independent_detail_areas`; `test_action_panel_keeps_quick_filter_and_transaction_details_separate`; `test_log_analyzer_updates_details_independently_and_clears_stale_data` |
| `test_vehicle_selector` | `test_refresh_table_resets_filtered_view_without_reanalysis`; `test_vehicle_manager_has_display_names_import_button` |

Các kỳ vọng lỗi gồm green highlight so với blue theme hiện tại, Save/Save Panel,
minimum button height, khoảng trắng detail text, filtered row count và label
Import Display Names/Import File Display Names. Không sửa các module/tab khác để
làm xanh test ngoài phạm vi. Không tuyên bố toàn bộ repository test suite green.

## Giới hạn còn lại

- Chưa kiểm thử phần cứng Vector thật; yêu cầu hardware acceptance M02 vẫn còn.
- Không có ảnh gốc/bốn source `.diag` thật để đối chiếu; chỉ verified schema
  được cung cấp và synthetic equivalents, gồm file VIN 16 steps.
- Visual QA offscreen + scale 150% không thay thế thao tác manual trên Windows/DPI thật.
- Native JSON format không có Vehicle association; view preferences nhớ tên
  Vehicle, không nhét ECU configuration vào sequence. Paths hiện là absolute;
  di chuyển project/external files cần Load lại và Save Order.
- File import/table population đồng bộ như native sequence editor, chưa tối ưu
  cho sequence hàng chục nghìn rows. Monitor là bounded display contract, chưa
  có benchmark cho live traffic và không có RX thread.
- Splitter/column sizes chưa persist; dùng defaults responsive mỗi lần mở.
- Có guard unsaved khi đổi/load document; không bổ sung application-wide close
  workflow cho unsaved sequence trong milestone UI này.
- Các baseline failures nêu trên cần xử lý riêng. Không TX/RX, ISO-TP, UDS runner,
  Seed-Key, flashing, CSV exporter hoặc actual BLF logging trong M03.

Nguồn API đối chiếu: [Qt QSplitter](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSplitter.html)
cho splitters/stretch/sizes; [Qt QAbstractItemView](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QAbstractItemView.html)
cho InternalMove, drop indicator và selection. Palette, controls, business rules và
persistence patterns lấy từ source V-CODE hiện có.
