V-CODE v3.0.6
EEIV Diagnostic Tool
AES EEIV by DAT TRAN

============================================================
1. GIỚI THIỆU
============================================================

V-CODE là công cụ hỗ trợ kỹ sư ô tô phân tích dữ liệu chẩn đoán,
Coding Value và dòng điện Sleep Current của xe.

Các chức năng chính:
- Phân tích CAN/UDS diagnostic log.
- Tìm kiếm và lọc Request/Response theo ECU.
- Phân tích và so sánh Coding Value.
- Tính toán CRC và chuyển đổi dữ liệu.
- Phân tích Q Current / Sleep Current.
- Quản lý Vehicle và ECU.
- Xuất báo cáo Excel.


============================================================
2. LOG ANALYZER
============================================================

Dùng để phân tích CAN/UDS diagnostic log.

Chức năng:
- Đọc file ASC/BLF.
- Chọn Vehicle và Log Channel.
- Phân tích UDS Request/Response.
- Xác định ECU theo Request/Response ID.
- Hiển thị Response Time và trạng thái transaction.
- Search dữ liệu.
- Tạo và sử dụng Quick Filter.
- Copy Request / Response / Transaction.
- Export báo cáo Excel.


============================================================
3. CODING VALUE
============================================================

Dùng để đọc, chỉnh sửa và kiểm tra Coding Value của ECU.

Chức năng:
- Hỗ trợ nhiều Coding Panel độc lập.
- Load Coding Definition.
- Decode Raw Value thành giá trị dễ đọc.
- Chỉnh sửa Raw Value hoặc Decoded Value.
- Preview payload.
- Highlight dữ liệu thay đổi.
- So sánh giá trị Before / After.
- Hiển thị MATCH / No-M.
- Search và filter Parameter.
- Nhận CRC từ CRC_Converter.
- Copy payload.
- Export báo cáo Excel.


============================================================
4. CRC_CONVERTER
============================================================

Cung cấp các công cụ xử lý dữ liệu nhanh.

CRC:
- Tính CRC8_SAE_J1850.
- Copy CRC.
- Transfer CRC sang Coding Value.

Converter:
- HEX
- Decimal
- ASCII
- Binary
- TXT
- Octa

QR Code:
- Tạo QR Code từ nội dung nhập vào.
- Preview và Copy QR Code.


============================================================
5. Q CURRENT
============================================================

Dùng để phân tích dòng điện Sleep Current của xe.

Hỗ trợ:
- Import dữ liệu CSV/XLSX.
- Lưu và chọn lại dataset đã Import.
- Cấu hình Standard Current.
- Cấu hình Wake Up Limit.
- Cấu hình Wake Duration.
- Chọn khoảng thời gian cần phân tích.
- Sampling Duration.

Current Chart hỗ trợ:
- Zoom và Scroll.
- Fit All.
- Pin.
- Cursor A/B.
- Đo Delta Time / Delta Current.
- Capture.
- Invert Y Axis.
- Hiển thị Sleep Limit.
- Highlight Wake-up Event.

Kết quả phân tích:
- PASSED / FAILED.
- Average Sleep Current.
- Minimum Current.
- Maximum Current.
- Wake-up Events.
- Start / End Time.
- Duration.
- Total Samples.
- Sample Interval.

Có thể Export báo cáo Excel gồm dữ liệu, kết quả phân tích
và Current Chart.


============================================================
6. VEHICLE MANAGER
============================================================

Dùng để quản lý Vehicle và ECU.

Chức năng:
- Create / Delete Vehicle.
- Add / Delete ECU.
- Chỉnh sửa thông tin ECU.
- Quản lý Request ID / Response ID.
- Import ECU List.
- Export Vehicle.
- Import Display Names.
- Import Rules Display Names.
- Cấu hình Keyboard Shortcuts.


============================================================
7. LICENSE & SUPPORT
============================================================

V-CODE sử dụng license để quản lý quyền sử dụng.

Nếu license hợp lệ:
- Các chức năng được cấp quyền sẽ hoạt động bình thường.

Nếu license không hợp lệ hoặc hết hạn:
- V-CODE sẽ chuyển sang Limited Mode.

Thông tin hỗ trợ:

Email:
tranducdat.eng@gmail.com
tranducdatks95@gmail.com

Phone:
0329000529


============================================================
8. REPORT
============================================================

Các báo cáo được lưu trong thư mục:

output/Report_LogAnalyzer/

output/Report_CodingValue/

output/Report_QCurrent/

Nếu không Export được report:
- Kiểm tra file Excel cũ có đang mở hay không.
- Đóng file Excel và thử Export lại.


============================================================
9. THÔNG TIN PHIÊN BẢN
============================================================

Application:
V-CODE v3.0.6

Product:
EEIV Diagnostic Tool

Platform:
Windows 10/11 x64

Developer:
DAT TRAN - AES EEIV

============================================================
END
============================================================