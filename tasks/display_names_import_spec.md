# Spec: Import display names from Vehicle Manager

## Objective
Cho phép người dùng chọn một file `display_names.json` từ tab Vehicle Manager và cập nhật mapping hiển thị UDS dùng chung của ứng dụng.

## Acceptance criteria
- Có nút `Import Display Names` trong Vehicle Manager.
- Có thêm option `Import Display Rules` để nhập nhiều dòng theo dạng `PAYLOAD|Display Name`.
- Payload được chuẩn hóa khoảng trắng, chữ hoa và số byte hex trước khi ghi.
- Rule mới được thêm; rule trùng được cập nhật tên hiển thị.
- File được chọn phải là JSON object mapping; mỗi giá trị phải chứa `display_name` là chuỗi không rỗng.
- File không hợp lệ không được ghi đè cấu hình hiện tại và phải hiển thị cảnh báo.
- File hợp lệ được ghi vào `config/display_names.json` và mapping được nạp lại ngay trong phiên chạy.
- Hủy hộp thoại không làm thay đổi dữ liệu.
- Vehicle Manager và chức năng Import ECU hiện tại không thay đổi hành vi.

## Verification
- Unit test validator/import bằng file tạm.
- Unit test parser rule, chuẩn hóa khoảng trắng và merge/update mapping.
- Unit test reload mapping trong `core.uds_lookup`.
- Chạy toàn bộ test suite bằng Python trong `.venv`.
- Kiểm tra cú pháp các file Python đã sửa.

## Boundaries
- Không sửa dữ liệu vehicle/ECU JSON.
- Không thêm dependency.
- Không commit file cấu hình người dùng hoặc file tạm.
