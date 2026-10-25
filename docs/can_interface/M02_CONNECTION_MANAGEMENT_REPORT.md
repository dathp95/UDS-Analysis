# CAN Interface M02 — Vector Connection Management

Ngày: 2026-10-25. Triển khai theo `.codex/skills/can-m02-connection/SKILL.md`.
Không commit/push; không triển khai M03, CAN TX/RX, ISO-TP, UDS hoặc sequence runner.

## Baseline và kết quả review

Baseline M01: `604dfe4020f10e3c8786e76ecc6463e2bb3f482b`
(`can interface - comit 54`). Commit trước đó `a7024fb` cũng mang tên `commit 54`;
baseline M01 được xác định theo hash trong skill. Đã xem source service/backend,
config/model, GUI, discovery worker, các test M01, báo cáo M01, threading pattern,
dependency pin và lifecycle MainWindow/application trước khi chỉnh sửa.

Những điểm cần sửa từ M01:

1. Connect/Disconnect gọi native driver đồng bộ từ GUI.
2. Connect lần hai tự đóng bus đang chạy.
3. Disconnect xóa reference trước khi biết cleanup thành công.
4. Label GUI tham gia quyết định trạng thái; service chưa có state machine/operation lock.
5. Global index từ snapshot cũ có thể trỏ tới hardware khác sau hotplug.
6. python-can 4.6.1 `VectorBus.shutdown()` suppress `VectorError` quanh nhóm cleanup:
   lỗi deactivate có thể làm bỏ qua close port và close driver.

## Kiến trúc và quyết định

Giữ `CANInterfaceTab → CANService → VectorBackend → python-can → XL Driver`.
Thêm `CANConnectionTask/Worker` giữa thao tác GUI và service; worker không truy cập
widget. Không thay layout top row, các control theme hoặc Diagnostic Sequence widgets.

Một QThread được tạo lười ở Connect đầu tiên và dùng lại xuyên Connect/Disconnect/
Reconnect. Mở và đóng bus trên cùng owner thread; không tạo thread riêng cho mỗi thao tác.
Discovery M01 giữ task riêng, nhưng service lock ngăn overlap discovery và connection.
Không tự gọi Refresh từ Connect hay tự chọn kênh khác khi thất bại.

## File thay đổi

| File | Nội dung |
|---|---|
| `services/can/can_connection.py` (mới) | Enum state, immutable snapshot và connection error có recovery/rediscovery flags |
| `services/can/can_config.py` | Metadata hardware tùy chọn cho revalidation |
| `services/can/can_service.py` | State machine, snapshot, khóa operation/state, validation, active config và recovery |
| `services/can/vector_backend.py` | Target revalidation, chống duplicate open, publish sau init, cleanup có xác nhận, error code |
| `services/can/owned_vector_bus.py` (mới) | Adapter hẹp cho lifecycle VectorBus 4.6.1, theo dõi resource của bus |
| `services/can/__init__.py` | Export state/snapshot mới; giữ export CANConnectionError cũ |
| `gui/workers/can_connection_worker.py` (mới) | Persistent owner thread, kết quả có token, shutdown tuần tự |
| `gui/workers/can_discovery_worker.py` | Cleanup wrapper sau native teardown, shutdown bơm event và dispose idempotent |
| `gui/tabs/can_interface_tab.py` | Connect/Disconnect bất đồng bộ, control theo state/busy, tooltip active target, cleanup |
| `tests/services/test_can_connection.py` (mới) | State, overlap, recovery, identity, dependency, error codes |
| `tests/services/test_owned_vector_bus.py` (mới) | Constructor VectorBus thật với XL functions giả lập; partial cleanup |
| `tests/services/test_vector_discovery.py` | Thêm snapshot đúng cho test connection metadata hiện có |
| `tests/gui/test_can_connection_worker.py` (mới) | Affinity, duplicate/late result, terminal outcome và shutdown |
| `tests/gui/test_can_connection_tab.py` (mới) | Slow operations, controls, unplug, recovery/theme và app quit subprocess |
| `tests/gui/test_can_interface_tab.py` | Chờ kết quả async trong các test M01 và cleanup task sau test |
| `docs/can_interface/M02_CONNECTION_MANAGEMENT_REPORT.md` (mới) | Báo cáo này |

Thư mục skill M02 đã untracked trước khi làm việc và được giữ nguyên. Không sửa
MainWindow, licensing, dữ liệu/config xe, dependency, database hoặc tab khác.

## State machine và public API

`CANService.snapshot` trả `CANConnectionSnapshot` frozen gồm `state`, `config`,
`error`, `rediscovery_required`. Enum `CANConnectionState` là nguồn trạng thái,
không lấy label làm nguồn quyết định.

| Từ | Sang | Điều kiện |
|---|---|---|
| DISCONNECTED / ERROR | CONNECTING | Config hợp lệ, không operation khác, không yêu cầu rediscovery |
| CONNECTING | CONNECTED | Constructor hoàn tất, bus được publish |
| CONNECTING | ERROR | Mở thất bại nhưng cleanup xác nhận sạch |
| CONNECTING | RECOVERY_REQUIRED | Partial cleanup lỗi hoặc không xác nhận được ownership |
| CONNECTED | DISCONNECTING | Chấp nhận Disconnect |
| DISCONNECTING | DISCONNECTED | Cleanup thành công |
| DISCONNECTING | RECOVERY_REQUIRED | Cleanup thất bại |
| ERROR | DISCONNECTED | Refresh thành công hoặc xác nhận trạng thái sạch qua Disconnect |
| DISCONNECTED / ERROR | RECOVERY_REQUIRED | Driver snapshot cleanup thất bại |

Disconnect khi đã DISCONNECTED là no-op. Operation lock acquire không blocking;
duplicate/concurrent Connect, Disconnect hoặc Refresh bị từ chối ngay. Snapshot
được bảo vệ bằng khóa riêng, đọc state không phải đợi native operation.

RECOVERY_REQUIRED không có retry tự động và không cho mở bus mới. Giữ reference
owner/config để không báo nhầm đã đóng sạch; yêu cầu khởi động lại V-CODE. Nếu chỉ
hardware mất/identity đổi và cleanup sạch, `rediscovery_required` chặn Connect đến
khi Refresh thành công. Disconnect không xóa yêu cầu rediscovery này.

## Cấu hình và đúng device/channel

Giữ các model M01 và constructor cũ `CANConfig("vector", 0, 500000)`.
Thêm `hw_type=None`, `hw_index=None`, `hw_channel=None` ở cuối dataclass frozen.
UI chốt config từ item data lúc Connect, gồm local channel, global index, serial,
hardware type/index/channel và bitrate. Không suy index từ text `CAN 1`.

Backend query snapshot driver hiện tại trước khi mở target có global index, kiểm
tra đúng một record global index, CAN capability, local channel và mọi identity
field đã cung cấp. Thiết bị bị tháo hoặc global index bị gán lại sẽ bị từ chối;
không đổi target, không cập nhật combo như một Refresh ngầm. Thiếu global index
hoặc hardware identity đáng tin cậy từ lựa chọn GUI thì Connect bị vô hiệu hóa.

Bus nhận local `channel`, `serial`, explicit global `channel_index`, bitrate,
`app_name=""` như M01. Hardware type/index/channel dùng để revalidate, không truyền
kwargs không được hỗ trợ vào VectorBus. Constructor cũ không metadata vẫn dùng
đường resolve global channel hiện có của python-can.

## Native resource cleanup

Default backend dùng subclass rất hẹp của VectorBus đang cài, thay vì mở qua
factory `can.Bus`. Điều này cho phép giữ object trước khi `__init__` chạy để xử lý
partial init và tránh config môi trường âm thầm đổi tham số kết nối. Test factory
`can_module.Bus` vẫn inject được; factory ngoài raise trước khi trả object được
xem là ownership không chắc chắn.

Adapter chỉ bọc instance driver reference, không patch module global, không tạo
ctypes/binding mới. Theo dõi `xlOpenDriver`, handle hợp lệ từ `xlOpenPort`, activation.
Shutdown thử deactivate rồi close port; close port thành công xác nhận channels đã
deactivate. Sau đó đóng driver. Chỉ xóa reference backend sau cleanup thành công.
Port close lỗi giữ owner và không tiếp tục đóng driver bên dưới port chưa xác nhận.
Driver close lỗi cũng giữ recovery. Không retry native handle sau cleanup lỗi;
finalizer không gọi driver trên GC thread tùy ý. Deactivation lỗi được log kể cả
khi port close tiếp theo thành công. Giữ nguyên exception cause/traceback.

## Thread lifecycle và GUI

GUI giữ `Connecting`/`Disconnecting` và khóa control ngay khi task được chấp nhận;
chỉ báo Connected sau constructor trả về. Tooltip hiển thị SN, HW identity, local
channel, global index và bitrate từ active config. Token và closed guard bỏ late
result; một operation có một terminal outcome cùng signal `finished`.

Khi đóng tab/application, xếp cleanup sau operation đang chạy trên cùng owner
thread, rồi quit. Task do application sở hữu nên tab bị hủy không hủy thread còn
chạy. `aboutToQuit` dùng local event loop để tiếp tục dispatch sự kiện trong lúc
cleanup; không gọi `terminate()` hoặc `wait()` vô hạn trên GUI. Đã kiểm tra đường
`QApplication.exec → quit → aboutToQuit` thật trong subprocess với Connect chậm.

Stress GUI từng tái hiện native abort/access violation trong discovery teardown.
M02 giữ worker/thread wrapper tới khi `thread.wait(0)` xác nhận native teardown
đã xong; nếu chưa xong thì QTimer kiểm tra lại. Không block GUI. Đã qua 180 lượt
test GUI lặp sau thay đổi; không tuyên bố đã xác định toàn bộ nguyên nhân native
bên trong PySide. M01 discovery schema và quy tắc giữ selection không thay đổi.

## Lỗi và hardware loss

Phân biệt dependency thiếu, driver không tải được, target không còn tồn tại,
mapping đổi, channel invalid/busy, bitrate không hợp lệ, init lỗi và cleanup lỗi.
Ưu tiên XL error code (120/129 hardware, 111/112/147/204 channel/access,
116/158 busy/init access, 201 driver), sau đó mới dùng fallback text cũ. Lỗi bất
ngờ có thông báo ngắn và log chi tiết. Recovery control không được mở lại chỉ vì
label đổi màu hay theme refresh.

Không có hardware monitoring/polling. Unplug được xử lý khi snapshot/open/cleanup
thực sự báo lỗi. Sau clean Disconnect không còn dùng bus; nếu port/driver không
đóng được thì giữ recovery, không giả vờ Disconnected.

## Xác minh tự động

Baseline: python-can **4.6.1**, PySide6 **6.11.1**, đúng pin trong requirements.
Tất cả phần cứng/XL functions được giả lập; không có CI hardware requirement.

- RED ban đầu: 5 tests thất bại (2 assertion + 3 chưa có state API), chứng minh
  duplicate Connect tự thay bus và shutdown lỗi làm mất reference.
- Increment service/backend đầu: 33 tests PASS; adapter/constructor: 39 tests PASS.
- GUI M01 lặp 10 vòng sau fix teardown: **180 lượt PASS**, 23.410 s.
- Worker/discovery/GUI M02 tập trung: **14 tests PASS**, 1.220 s.
- Hồi quy gộp CAN M01/M02 + Diagnostic Sequence table/list/repository:
  **131 tests PASS**, 10.961 s trước review cuối. Kết quả sau review được ghi dưới đây.
- `compileall` và `git diff --check`: PASS tại thời điểm review.

Coverage gồm Connect/Disconnect/reconnect; duplicate và overlap hai chiều; Refresh
khi busy; config/identity invalid; global index bị gán lại; mất dependency/driver;
unplug trước/during init; lỗi open port/activation; partial init; lỗi close port/
driver; recovery và rediscovery; heartbeat GUI khi native chậm; config không đổi
dù widget bị cập nhật programmatically; late result; close tab và app quit khi
đang Connect; Light/Dark recovery; M01 và Diagnostic Sequence regression.

### Kết quả sau review cuối

**133 tests PASS, 0 failed, 0 skipped, 6.158 s.** Bao gồm test 30 lần discovery
teardown trong cùng process, test recovery message khi snapshot driver không đóng
được, và application quit subprocess. Không tắt logging toàn cục; assertLogs của
M01 vẫn được thực thi. Không có phần cứng Vector thật trong lần chạy này.

Các module chạy bằng `unittest`:

```text
tests.services.test_can_connection
tests.services.test_owned_vector_bus
tests.services.test_can_service
tests.services.test_vector_discovery
tests.gui.test_can_interface_tab
tests.gui.test_can_connection_tab
tests.gui.test_can_connection_worker
tests.gui.test_can_discovery_worker
tests.gui.test_diagnostic_sequence_table
tests.gui.test_diagnostic_sequence_list
tests.repositories.test_diagnostic_sequence_repository
```

Runner dùng `python -X faulthandler`, `unittest.defaultTestLoader.loadTestsFromNames`
cho các module trên và `TextTestRunner(verbosity=1)`. `tempfile.tempdir` được đặt
vào một `TemporaryDirectory(dir=Path.cwd())` trong suốt test, rồi khôi phục/xóa
thư mục tạm. GUI dùng `QT_QPA_PLATFORM=offscreen`. Compile và whitespace check
được chạy lại trên phiên bản bàn giao.

## Hardware acceptance — còn phải thực hiện

Trên Windows có XL Driver và VN1630A/VN1640A, dùng bench/test network đúng cấu hình:

- [ ] Khởi động không hardware; Refresh không tạo device giả.
- [ ] Cắm hardware; đúng tên/SN và các local/global channel.
- [ ] Hai thiết bị cùng model; chọn từng thiết bị/kênh và xác nhận port thực tế.
- [ ] Connect đúng bitrate; Disconnect; Reconnect nhiều lần.
- [ ] Disconnect, đổi channel, Connect lại; Refresh vẫn giữ selection đúng.
- [ ] Rút hardware trước Connect; lỗi rõ, yêu cầu Refresh, không chọn kênh khác.
- [ ] Rút hardware lúc Connected rồi Disconnect; kiểm tra clean/recovery outcome.
- [ ] Kênh đang dùng bởi ứng dụng khác: kiểm tra init access/busy và bitrate.
- [ ] Đóng tab/application lúc Connecting, Connected và Disconnecting.
- [ ] Light/Dark trong các state, layout/status/tooltip trên desktop thật.
- [ ] Restart V-CODE và lặp lại.

**Chưa chạy hardware acceptance**; test mock không chứng minh hardware thật hoạt
động. Không phát frame tùy ý lên xe sản xuất trong M02.

## Giới hạn và sẵn sàng cho M03

- Native XL call không có cơ chế hủy cưỡng bức an toàn. Nếu driver treo, shutdown
  có thể tiếp tục chờ trong event loop; không có hard deadline/force thread kill.
- Revalidation và open không phải giao dịch atomic của XL; hotplug ngay giữa hai
  bước vẫn phải dựa vào lỗi native. Không bảo đảm phát hiện thiết bị bị thay bằng
  thiết bị có toàn bộ identity trùng hệt.
- Adapter phụ thuộc lifecycle python-can 4.6.1 đã pin. Nâng version cần review
  constructor/shutdown và chạy lại test boundary. Chỉ theo dõi resource của instance;
  không sửa helper `get_channel_configs()` nội bộ upstream, vốn có thể suppress lỗi
  và không bảo đảm finally-close ở query snapshot phụ. Cần kiểm thử driver thật
  cho các lỗi hiếm của helper này; không tuyên bố loại bỏ mọi leak nội bộ upstream.
- Khi cleanup không xác nhận được, recovery hiện là restart, không có nút retry
  cleanup hoặc tự reconnect. Không có continuous unplug detection khi idle.
- Test GUI offscreen xác minh logic/theme/layout, chưa xác minh pixel/font và
  thao tác desktop thật. Chưa chạy toàn bộ test suite của mọi tab ngoài phạm vi.
- M03 có thể dùng owner worker/state hiện tại để thiết kế TX/RX có serialization,
  hardware-loss reporting và shutdown riêng. Chưa có API TX/RX hay runner trong M02.

## Nguồn đối chiếu

- [python-can 4.6.1 VectorBus source](https://python-can.readthedocs.io/en/stable/_modules/can/interfaces/vector/canlib.html):
  constructor mapping, activation failure và shutdown suppression; đối chiếu source đang cài.
- [Qt for Python QThread](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html):
  QObject worker, queued signal và khác biệt finished/native cleanup.
- `docs/can_interface/XL_Driver_Library_Manual_EN.pdf`, version 20.30, đọc trang
  PDF 37, 39–41, 44–45. Trang 44 xác nhận xlClosePort cũng deactivate channels;
  không tuyên bố đã đọc toàn bộ manual hoặc xác minh repository CBT từ xa.

Suggested commit message, chưa tạo commit:
`CAN Interface - M02 Vector Connection Management`.
