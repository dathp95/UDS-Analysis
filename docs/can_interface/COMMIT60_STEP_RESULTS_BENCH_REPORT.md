# Commit 60 — Step Results và Trusted Bench Session

Ngày: 2026-10-26. Baseline: commit 59,
`4cf5c360220cfcd44f416c9e58fa828c4a2aa926`.
Không tạo commit/push.

## Issue A: nguyên nhân và thay đổi

`CanDiagnosticTablePanel._mark_dirty()` trước đây xóa toàn bộ `_runtime` dù chỉ
một step thay đổi. Runtime hiện được đối chiếu theo stable `step_id` với signature
`(ecu, request, expected_response, match)`.

| Thao tác | Runtime sau thay đổi |
|---|---|
| Đổi ECU/request/expected/match | Chỉ xóa kết quả của step đó |
| Sửa comment/delay/repeat | Giữ các kết quả manual đã hoàn tất |
| Thêm/xóa row | Giữ kết quả gắn với ID còn tồn tại; chỉ loại ID đã xóa |
| Load sequence | Runtime mới, UUID mới cho document mới |
| Đổi Vehicle/configuration refresh hoặc direct `fn_set_vehicle` | Xóa toàn bộ runtime cũ để không trình bày kết quả từ cấu hình khác |

Normal single-row edit không cấp lại ID hoặc rebuild toàn bảng. Các cell của row
không đổi giữ nguyên identity. So sánh signature là thao tác dữ liệu Python; chỉ
row bị invalidation được render lại. Native table vẫn quản lý dirty/save state.

Generation/cancellation giữ chính sách bảo thủ M04: bất kỳ definition edit nào
cũng hủy request đang chạy và loại late result. Runtime Running của request bị
hủy được xóa riêng, tránh để trạng thái Running tồn tại sau metadata edit. Các
kết quả completed khác vẫn được giữ.

## Issue B: UI confirmation tách khỏi backend authorization

Nút **Trusted Bench: OFF/ON** nằm ở header Connection, dùng ActionButton/theme
hiện có. Mặc định OFF, không có persistence. Bật cần xác nhận một lần với Vehicle,
CAN port/serial hiện tại và ý nghĩa ba thao tác; mặc định dialog là No.

Grant chỉ bao gồm **đúng từng byte**:

- `10 01`: Default Session.
- `10 03`: Extended Session.
- `14 FF FF FF`: Clear all DTCs.

Không nới toàn bộ SID 10 hoặc 14. `10 81`, `10 04`, `10 03 00`, nhóm DTC khác,
`11`, `2E`, `31`, `85` vẫn cần xác nhận riêng như trước. 0x27 và programming
restrictions không đổi.

`CANService` cấp immutable `TrustedBenchAuthorization` trong RAM, gắn connection
UUID và Vehicle. Chỉ `fn_confirm_trusted_request()` mới chuyển một request trong
phạm vi grant thành `confirmed=True` kèm authorization ID. Request ngoài phạm vi
trả về None để controller đi qua dialog manual cũ.

`validate_send_policy()` vẫn chạy; field bench ID chỉ được phép cho exact
allowlist và request đã confirmed. Khi worker nhận transaction,
`fn_begin_diagnostic()` kiểm tra lại grant ID, Vehicle và connection UUID trước
khi nhận lease; token giả, revoked/reissued hoặc từ connection cũ đều bị từ chối.
Manual confirmation hiện có vẫn là một đường xác nhận riêng, không giả làm grant.

Grant bị thu hồi khi bắt đầu connection operation, service rời CONNECTED,
Disconnect/reconnect, close hoặc Vehicle/configuration refresh. Modal approval
kiểm tra lại generation/Vehicle/connection sau khi người dùng trả lời để tránh
cấp quyền vào context đã thay đổi. Click nút ON thu hồi quyền ngay; button bị
disable khi đang request hoặc đang chuẩn bị confirmation.

Không thay đổi Vector native ownership, RX consumer, ISO-TP engine, continuous
monitor, recorder/BLF writer, ECU resolver hoặc automatic execution.

## File thay đổi

| File | Vai trò |
|---|---|
| `gui/widgets/can_interface/diagnostic_table_panel.py` | Step signatures, scoped invalidation, Vehicle reset |
| `gui/controllers/can_diagnostic_controller.py` | Giữ cancellation, cấp quyền qua UI và sử dụng grant backend |
| `core/diagnostic_request.py` | Exact allowlist, immutable grant và transient authorization ID |
| `services/can/can_service.py` | Backend issuance, revocation và admission validation; không đổi native I/O |
| `gui/widgets/can_interface/connection_panel.py` | Nút trạng thái/opt-in theo theme |
| `gui/tabs/can_interface_tab.py` | Wire nút vào controller |
| `tests/gui/test_can_step_runtime.py` (mới) | Row edits, metadata, add/delete, Vehicle/load reset |
| `tests/gui/test_can_trusted_bench.py` (mới) | Opt-in, send/no-popup, restrictions, reconnect, context races, E2E bốn kết quả VIN |
| `tests/services/test_trusted_bench_session.py` (mới) | Backend grant scope, forged/revoked/stale IDs, app-instance default |
| `tests/gui/test_can_diagnostic_table_panel.py` | Cập nhật yêu cầu comment giữ Passed; payload edit invalidates |
| `tests/gui/test_can_interface_tab.py` | Fake service hỗ trợ revocation contract |
| `docs/can_interface/COMMIT60_STEP_RESULTS_BENCH_REPORT.md` | Báo cáo này |

`config/can_interface_ui.json` đã có thay đổi trước task và được giữ nguyên trong
worktree; không nằm trong implementation patch.

## Verification thực tế

- **240 PASS, 0 FAIL, 0 ERROR** trong 21,426 giây: CAN M01/M02/M03/M04/M04B,
  Commit 59 sidebar, native sequence, BLF reader/channel/pipeline và 13 test mới
  của Commit 60. Chạy bằng project `.venv`, `unittest.defaultTestLoader` và root
  NullHandler cho các fault injection; không disable logging toàn cục.
- Sau đó bổ sung assertion revoke trong cùng connection: **3/3 backend PASS**.
- `py_compile`: **11 file Python thay đổi** compile thành công.
- `git diff --check`: pass; chỉ có Git line-ending notices thông thường.
- Review độc lập: không phát hiện thêm authorization/race/lifecycle finding;
  có probe cho revoke/reissue, Vehicle mismatch và release lock khi bị từ chối.
- Bốn ảnh fake-bus QA tại `output/qa_can_commit60/`, Light/Dark,
  1366×768 và 1600×900. Step 1–4 Passed với VIN payload gốc, Step 5 EPS, trạng
  thái Trusted Bench ON đọc được. Đây không phải capture từ xe thật.

Lệnh focused có thể chạy lại từ workspace:

```powershell
.venv\Scripts\python.exe -m unittest `
  tests.gui.test_can_step_runtime tests.gui.test_can_trusted_bench `
  tests.services.test_trusted_bench_session `
  tests.gui.test_can_diagnostic_table_panel tests.gui.test_can_diagnostic_execution
```

Full regression còn gồm toàn bộ `test_can_*`, `test_isotp_transport`,
`test_diagnostic_client`, `test_ecu_diagnostic_resolver`, `test_owned_vector_bus`,
`test_vector_discovery`, native Diagnostic Sequence GUI/repository/import và
`test_blf_reader`, `test_log_channels`, `test_pipeline_channel_flow`.

## Giới hạn / trade-off

- Kiểm thử GUI Qt offscreen và fake bus; chưa thử Commit 60 trên Vector/ECU thật.
- Bench authorization dựa trên xác nhận rõ ràng của operator; ứng dụng không tự
  chứng minh được dây/kênh đang nối vào bench thay vì một xe khác.
- Grant hết hạn cả khi refresh cấu hình cùng tên Vehicle, để tránh giữ quyền hoặc
  kết quả cũ sau thay đổi ECU mapping.
- Vẫn hủy request đang chạy khi sửa definition ở row khác; đây là generation
  protection bảo thủ được giữ từ M04, không phải automatic sequence behavior.
- Không chạy toàn bộ suite các tab không liên quan. Không thêm/chạy Security
  Access, seed-key DLL, flashing hoặc automatic execution.

Suggested commit title (không tự commit):
`can interface - commit 60: Preserve Step Results and Improve Diagnostic Confirmation UX`
