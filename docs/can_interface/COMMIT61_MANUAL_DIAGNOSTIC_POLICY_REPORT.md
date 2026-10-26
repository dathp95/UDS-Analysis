# Commit 61 — Connection-scoped Manual Diagnostic Authorization

Ngày: 2026-10-26. Baseline Commit 60:
`8f158a973eb19eae6881faa00e7fbc1242e19eab`.
Không tạo commit/push.

## Hành vi người dùng

Đã bỏ nút Trusted Bench ON/OFF, toggle handler và popup cấp quyền của
CanDiagnosticController. Header Connection có lựa chọn policy trước Connect:

1. **Standard: confirm state changes** — mặc định; không có quyền bench.
2. **I authorize test-bench diagnostics** — operator chủ động cấu hình kết nối
   test bench. Tooltip nêu rõ các payload, bao gồm thao tác clear all DTCs.

Sau khi chọn policy thứ hai rồi Connect, manual `>` cho đúng `10 01`, `10 03`,
`14 FF FF FF` không có popup từng request. Mở/refresh/chuyển sequence hoặc chọn
Vehicle không thu hồi quyền của kết nối đó. Vehicle Manager vẫn là nguồn TX/RX
CAN IDs cho từng request, không lấy địa chỉ từ authorization context.

Selector bị khóa trong lúc kết nối. Disconnect/fault/failure reset selector về
Standard; lần Connect kế tiếp cần chọn policy rõ ràng nếu muốn cấp quyền mới.
Policy/grant không được lưu ra file, và app mới khởi động ở Standard.
Các hộp thoại bảo vệ unsaved sequence vẫn giữ nguyên.

## Backend contract và scope

`CANConfig` có field tùy chọn `bench_context: BenchAuthorizationContext | None`.
Context immutable gồm `context_id` và `authorized`, mặc định False. Chỉ Connect
với context được duyệt rõ ràng mới có thể cấp grant. Bare Connect, có request,
refresh sequence, hoặc gọi hàm confirm đều không tự tạo quyền.

Grant gắn với native connection UUID và context ID, không gắn với document hay
Vehicle đang mở. Exact allowlist giữ nguyên; không mở rộng toàn SID 10/14:

| Request | Policy |
|---|---|
| `10 01`, `10 03`, `14 FF FF FF` | Được confirm bằng grant hợp lệ của connection/context hiện tại |
| `11`, `2E`, `31`, `85`, `10 81`, `10 03 00`, nhóm DTC khác | Vẫn cần manual confirmation như trước |
| `27`, programming requests đã bị chặn | Tiếp tục bị chặn; không có bypass bench |

`validate_send_policy()` tiếp tục chạy. Backend xác minh authorization ID,
connection generation và context tại admission **và ngay trước bench TX**.
Không gán `confirmed=True` cho request ngoài exact allowlist. Token giả, hết hạn,
hoặc từ connection/context cũ bị từ chối.

`fn_configure_bench_context()` giữ grant khi context không đổi; đổi context thu
hồi quyền ngay, nhưng không tự cấp quyền mới trên một connection đang mở.
Programmatic callers muốn cấp quyền dùng Connect với cấu hình context rõ ràng;
API cấp quyền theo Vehicle/toggle `fn_authorize_trusted_bench()` cũ đã được bỏ.

Thiếu generation hợp lệ cũng không cấp grant. Connection có thể vẫn hoạt động
theo policy manual thông thường; không giả định metadata thiếu là quyền hợp lệ.

## Race handling và cancellation

- Revision của authorization được snapshot trước native open. Đổi context hoặc
  revoke/close trong lúc Connect đang chờ khiến completion không được cấp lại
  grant cũ. Transition CONNECTED và grant publication dùng cùng state lock.
- Bench TX và revoke/context change được tuần tự hóa bằng lock riêng, theo thứ tự
  `bench_tx → state`. Không giữ state/snapshot lock qua native I/O. Non-bench TX
  giữ đường xử lý cũ.
- Revoke hoàn tất sau một bench send đã bắt đầu nếu send đó đang chạy; không thể
  thu hồi frame đã giao cho driver. Sau khi revoke hoàn tất không có bench TX mới
  vượt qua khoảng check/send bằng grant cũ.
- Revoke sau admission nhưng trước TX đi qua `DiagnosticCancelled`, không bị
  phân loại nhầm thành driver/capture fault. Monitor tiếp tục chạy, BLF vẫn có thể
  finalize hoàn chỉnh nếu không có lỗi/mất frame thực sự.
- Kiểu cancellation chuyển vào core và được import lại qua adapter ISO-TP để
  giữ alias tương thích. Không đổi segmentation/reassembly, FC, BS/STmin, timeout
  hoặc NRC logic.

## Bảo toàn Commit 60 / M04 / M04B

Không có diff trong runtime invalidation panel của Commit 60: ECU/request/
expected/match vẫn chỉ invalidate step liên quan, metadata giữ kết quả completed,
Vehicle/configuration change vẫn xóa runtime stale. Chỉ bỏ việc thu hồi **grant**
khi các event này phát ra; generation/cancellation của document vẫn hoạt động.

Không sửa Vector backend, native owner worker, RX consumer, CAN Monitor hay BLF
recorder. Không thêm automatic execution, raw TX, Security Access hoặc seed-key.

## File thay đổi

| File | Vai trò |
|---|---|
| `core/bench_authorization.py` (mới) | Typed explicit connection context |
| `core/diagnostic_request.py` | Grant theo context, shared cancellation type |
| `services/can/can_config.py` | Optional bench context, mặc định không cấp quyền |
| `services/can/can_service.py` | Cấp/revoke/validate grant, revision và TX serialization |
| `services/can/isotp_transport.py` | Import shared cancellation; giữ public alias, không đổi protocol engine |
| `gui/controllers/can_connection_controller.py` | Policy → config, lock/reset selector, status detail |
| `gui/controllers/can_diagnostic_controller.py` | Gỡ toggle/popup; chỉ revoke theo connection lifecycle/close |
| `gui/widgets/can_interface/connection_panel.py` | Selector config thay button ON/OFF |
| `gui/tabs/can_interface_tab.py` | Bỏ wiring button cũ |
| `tests/services/test_bench_connection_policy.py` (mới) | 9 test scope/expiry/race/serialization |
| `tests/gui/test_can_connection_bench_policy.py` (mới) | 5 test workflow/sidebar/repeated sends/revoke + BLF |
| `tests/services/test_trusted_bench_session.py` | Cập nhật expectation từ Vehicle grant sang connection context |
| `tests/gui/test_can_trusted_bench.py` | Thay các test toggle cũ, giữ regression 4 kết quả VIN và theme |
| `docs/can_interface/COMMIT61_MANUAL_DIAGNOSTIC_POLICY_REPORT.md` | Báo cáo này |

Thay đổi có sẵn ở `config/can_interface_ui.json` được giữ nguyên, không nằm trong
implementation patch.

## Verification thực tế

- Full CAN/UDS/M04/M04B/Commit59–61/native sequence/BLF reader regression:
  **254 PASS, 0 FAIL, 0 ERROR**, 49,023 giây.
- Backend policy/race sau bổ sung assertion Connect hoàn tất: **9/9 PASS**.
- Các test RED đã tái hiện được: thiếu connection policy, Connect khôi phục grant
  đã revoke, TX sau admission bằng quyền hết hạn, và race giữa check/TX/revoke.
- Test GUI chuyển bốn sequence qua sidebar/controller thật và refresh Vehicle
  trong cùng connection: gửi lặp exact allowlist mà không gọi QMessageBox.
- Test revoke ngay trước TX: Cancelled, không có native frame, monitor vẫn chạy,
  recorder finalize complete. Test 2 thread xác nhận revoke đợi bench TX và
  snapshot vẫn đọc được trong lúc fake native send chờ.
- Review độc lập cuối: không còn substantive finding; đã kiểm tra lock order và
  revision/lifecycle. Không tạo agent con hoặc sửa file trong lượt review.
- `py_compile`: **13 file Python thay đổi** pass. `git diff --check`: pass.
  Startup import vẫn graceful khi giả lập không có python-can.
- Visual QA fake bus: `output/qa_can_commit61/`, Light/Dark, 1366×768 và
  1600×900. Không có nút ON/OFF; selector policy không bị che/cắt.

Focused command:

```powershell
.venv\Scripts\python.exe -m unittest `
  tests.services.test_bench_connection_policy tests.services.test_trusted_bench_session `
  tests.gui.test_can_connection_bench_policy tests.gui.test_can_trusted_bench `
  tests.gui.test_can_step_runtime tests.services.test_isotp_transport tests.services.test_diagnostic_client
```

Full selection còn gồm toàn bộ CAN service/discovery/connection/owner tests,
CAN GUI/sidebar/workspace/model tests, native Diagnostic Sequence GUI/import/
repository và `test_blf_reader`, `test_log_channels`, `test_pipeline_channel_flow`.
Dùng project `.venv`, unittest và NullHandler cho fault injection; không disable
logging toàn cục. Không chạy suite các tab không liên quan.

## Giới hạn

Chưa kiểm thử Commit 61 trên Vector/ECU thật. Bench approval vẫn là xác nhận của
operator tại cấu hình kết nối; phần mềm không tự chứng minh được dây đang nối
bench thay vì xe khác. API caller cung cấp lại cấu hình được duyệt cho một Connect
mới có thể nhận grant mới; grant/token cũ vẫn hết hạn. GUI luôn reset lựa chọn sau
Disconnect và không lưu approval qua restart.

Native send dùng timeout 0 hiện có. Revocation chờ send đã bắt đầu kết thúc;
không thể cưỡng bức hủy vendor call nếu driver bị treo.

Suggested commit title (không tự commit):
`can interface - commit 61: Simplify Manual Diagnostic Confirmation`
