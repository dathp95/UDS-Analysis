# CAN Interface M01 — Vector Device Discovery

Ngày xác minh: 2026-10-25. Chỉ triển khai Milestone 01; không commit hoặc push.

## Kết quả và kiến trúc

Danh sách Device/Channel hardcoded được thay bằng discovery thực khi nhấn Refresh.
Giữ luồng `CANInterfaceTab → CANService → VectorBackend → python-can → XL Driver`,
layout, bitrate, Connect/Disconnect và các widget Diagnostic Sequence hiện có.
Không mở CAN bus hoặc phát CAN frame khi Refresh. Constructor không tải driver;
không cần phần cứng để tạo tab.

## Các file thay đổi

| File | Thay đổi |
|---|---|
| `services/can/can_device.py` (mới) | Model immutable và exception discovery |
| `services/can/can_config.py` | Thêm metadata kết nối tùy chọn, tương thích constructor cũ |
| `services/can/vector_backend.py` | Discovery, kiểm tra driver, chuẩn hóa metadata, truyền lựa chọn vào Bus |
| `services/can/can_service.py` | Delegate và kiểm tra contract discovery; chặn Refresh khi connected |
| `services/can/__init__.py` | Export model/exception mới |
| `gui/workers/can_discovery_worker.py` (mới) | Worker/task QThread và quản lý vòng đời |
| `gui/tabs/can_interface_tab.py` | Combo động, giữ lựa chọn, trạng thái nút, kết quả bất đồng bộ |
| `tests/services/test_can_service.py` | Regression và validation model/config |
| `tests/services/test_vector_discovery.py` (mới) | Driver/API giả lập, mapping, lỗi và không mở bus |
| `tests/gui/test_can_interface_tab.py` | Discovery/selection/refresh/theme/connection regression |
| `tests/gui/test_can_discovery_worker.py` (mới) | Thread affinity, lỗi, duplicate start và shutdown |
| `docs/can_interface/M01_DEVICE_DISCOVERY_REPORT.md` (mới) | Báo cáo này |

Không sửa dependency, schema database, diagnostic widgets, licensing hoặc module ngoài phạm vi.

## Contract và ánh xạ

- `CANChannelInfo(channel, channel_index, name, supports_fd, hw_channel=None)` và
  `CANDeviceInfo(name, serial, hw_type, hw_index, channels, discovery_id="")` là frozen
  dataclass; `channels` là tuple. Service trả `tuple[CANDeviceInfo, ...]`.
- `CANConfig` thêm `serial=None`, `channel_index=None` sau các field cũ. Cách gọi
  `CANConfig("vector", 0, 500000)` và field `fd` cũ vẫn hoạt động.
- Gom kênh theo `(serial, hw_type, hw_index)` khi đủ hardware type/index. Không gom
  bằng tên model hoặc serial đơn lẻ. Hai thiết bị trùng serial nhưng khác hardware
  index vẫn phân biệt. Metadata thiếu được cô lập theo global index/ordinal, tránh
  ghép nhầm các thiết bị. Global index trùng bị từ chối.
- Tên thiết bị lấy từ metadata driver (`vector_channel_config.name`), thiếu thì dùng
  `Vector Device`; không có bảng tự suy tên VN từ hardware type. Label thêm SN/HW
  hoặc index để phân biệt. Chỉ đưa kênh CAN-capable vào danh sách.
- Giữ nguyên native `channel`, `hw_channel` và global `channel_index`; label CAN
  dùng số local cộng một. Khi Connect, truyền `channel`, `serial`, `channel_index`
  đã chọn tới `can.Bus`, giữ `app_name=""` và bitrate hiện có. Trong python-can
  4.6.1, explicit global index được ưu tiên cho một kênh, kể cả khi serial trùng.
- Thiếu global index: vẫn hiển thị metadata nhưng vô hiệu hóa Connect để tránh
  chọn nhầm bus. Caller cũ không có metadata vẫn đi qua đường kết nối cũ.
- Refresh giữ device identity và local channel khi còn tồn tại, kể cả global
  index thay đổi. Hardware mất được loại khỏi combo; không tạo thiết bị giả.

## API thực tế và nguồn đã kiểm tra

Môi trường xác minh: **python-can 4.6.1**, **PySide6 6.11.1**. Không nâng dependency.
Đã đọc implementation đang cài của `detect_available_configs`, Vector detection,
`get_channel_configs`, `_get_xl_driver_config`, `_find_global_channel_idx`,
`VectorBus.__init__` và `VectorChannelConfig`.

Discovery dùng `can.detect_available_configs(interfaces=["vector"], timeout=None)`.
Schema thực tế có local `channel`, `serial`, global `channel_index`, `hw_type`,
`hw_index`, `hw_channel`, `supports_fd`, `vector_channel_config`.

`get_channel_configs()` của phiên bản này bắt `VectorError` rồi trả danh sách rỗng.
Do đó backend kiểm tra cấu hình driver trước qua binding XL sẵn có của python-can:
`xlOpenDriver → xlGetDriverConfig → xlCloseDriver` (close trong finally sau open
thành công). Không tạo ctypes binding mới, không gọi `xlOpenPort`, activation hay
`can.Bus` trong discovery. Kiểm tra này phân biệt lỗi driver, không hardware và
hardware không có kênh CAN. Public detection tiếp tục là nguồn metadata chính.

Tài liệu đối chiếu:

- [python-can Vector interface](https://python-can.readthedocs.io/en/stable/interfaces/vector.html).
- [python-can Vector implementation](https://python-can.readthedocs.io/en/stable/_modules/can/interfaces/vector/canlib.html).
- `docs/can_interface/XL_Driver_Library_Manual_EN.pdf`: đọc nội dung các trang PDF
  37, 39–41 bằng QtPdf; manual version 20.30, tổng 498 trang. Đối chiếu vòng đời
  driver, CAN capability, local hardware channel và global channel index.
- Có bản PDF tại `can_interface/XL_Driver_Library_Manual_EN.pdf`, không đọc riêng
  toàn bộ bản này. Không có `CBT/reference_docs/XL_Driver_Library_Manual_EN.pdf`
  trong workspace; không tuyên bố đã kiểm chứng repository CBT từ xa.

## Lỗi và vòng đời bất đồng bộ

Phân biệt `CANDependencyError`, `VectorDriverUnavailableError`,
`CANNoChannelsError`, `CANDiscoveryError`. Không hardware trả tuple rỗng và thông
báo `No Vector CAN device detected.`; lỗi driver không bị đổi thành “không thiết bị”.
Lỗi bất ngờ có thông báo ngắn, traceback/cause được giữ cho chẩn đoán. Nếu preflight
thấy CAN nhưng public detection rỗng thì báo kết quả không nhất quán để Refresh lại.

Hardware discovery chạy bằng QObject worker trên QThread, dựa trên mẫu task runner
hiện có. Worker không truy cập widget. Signal direct chỉ ghi kết quả Python vào
task; public result/error được chuyển trên GUI thread sau khi thread đã dừng,
không đọc dữ liệu từ QObject worker đã có thể bị xóa. Chặn Refresh đồng thời;
vô hiệu hóa Refresh khi connected ở cả GUI/service/backend. Late result không
ghi đè tab đã đóng hoặc cấu hình đã được kết nối từ nơi khác.

Task được application sở hữu để tab bị hủy không kéo theo QThread đang chạy.
Đóng tab đánh dấu bỏ kết quả và request interruption. Thoát application chờ native
call kết thúc, không terminate QThread. `timeout=None` tránh public API bỏ chờ rồi
để detection thread native tiếp tục chạy ngoài vòng đời task.

## Xác minh tự động

| Kiểm tra | Kết quả |
|---|---|
| CAN service/backend/GUI/worker | 50 tests PASS, 1.299 s |
| Các test trên + Diagnostic Sequence table/list/repository | **100 tests PASS**, 3.984 s |
| Worker suite lặp 20 vòng | **80 lượt test PASS**, 0.173 s |
| `compileall` các module/test thay đổi | PASS |
| `git diff --check` | PASS |

Tất cả hardware/API response trong test được mock hoặc fake. Có test gọi public
`can.detect_available_configs` đang cài với backend callback giả để xác minh
`timeout=None`; không kết nối driver thật. Dữ liệu tạm của hồi quy nằm trong workspace.

Coverage gồm: không hardware; một/nhiều kênh; nhiều thiết bị và serial trùng; không
CAN; thiếu dependency/DLL; driver query lỗi vẫn close; unexpected error; metadata
thiếu/trùng; Refresh không Bus/open port/activate/transmit; không phá active session;
giữ selection và bitrate; thiết bị bị tháo; duplicate Refresh; GUI heartbeat khi
discovery bị chặn; kết quả đến sau close; Light/Dark refresh; kết nối cũ và mới.

Trong quá trình xác minh có vòng chạy gộp kết thúc bất thường tại test QThread.
Đã bỏ đọc outcome từ worker ở callback cleanup và chuyển sang ghi nhận bằng signal
trước cleanup. Các vòng PASS ở trên được chạy sau thay đổi này; chưa có bằng chứng
để khẳng định nguyên nhân native của lần thoát trước đó.

## Giới hạn và kiểm thử phần cứng còn lại

- **Chưa kiểm thử VN1630A/VN1640A thật**; automated PASS không thay thế hardware
  acceptance. Cần xác minh Refresh, nhiều thiết bị, chọn kênh/bitrate, Connect/
  Disconnect và tháo thiết bị rồi Refresh trên Windows có XL Driver.
- GUI test chạy offscreen. Logic Light/Dark/layout được kiểm tra; chưa xác minh
  typography/pixel bằng desktop thật (môi trường offscreen không có font phù hợp).
- Không có hard timeout an toàn cho native XL call. Nếu driver treo, UI discovery
  vẫn chạy ngoài GUI nhưng application exit có thể phải chờ; không ép dừng thread.
- Preflight và discovery là hai snapshot: hotplug giữa chúng có thể gây thông báo
  không nhất quán và cần Refresh lại. Chỉ đảm bảo cleanup cho các XL call do backend
  này trực tiếp sở hữu, không thay implementation cleanup nội bộ của python-can.
- Khi hoàn toàn thiếu hardware identity, fallback ordinal không bảo đảm giữ lựa
  chọn qua thay đổi thứ tự. Thiếu global index thì Connect bị vô hiệu hóa.
- Refresh không chạy khi connected; không triển khai tự phát hiện hotplug active.

## Ranh giới Milestone 02

Không triển khai Milestone 02 hoặc chức năng TX/RX, monitor/logging, CAN FD data
path, ISO-TP/UDS, ECU scan, Diagnostic Sequence execution, Security Access hay flashing.
M01 đã truyền metadata discovery tới kết nối hiện có; không cần trì hoãn mapping
này sang M02. Công việc tiếp theo cần đặc tả M02 riêng và hardware acceptance;
`supports_fd` hiện chỉ là metadata, không bật truyền CAN FD.

Suggested commit message (chưa tạo commit):
`CAN Interface - M01 Vector Device Discovery`.
