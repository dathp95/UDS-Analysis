# Copy CRC Button

Date: 2026-08-12

## Request
Them button `COPY CRC` ben canh `txt_crc_output` trong tab CRC_Converter.

## Implementation
- Them `self.btn_copy_crc = PrimaryButton("COPY CRC", width=100)` canh `txt_crc_output`.
- Trang thai khoi tao: `COPY CRC` disabled khi `txt_crc_output` chua co du lieu.
- Khi calculate CRC loi: clear output va disabled `COPY CRC`.
- Khi calculate CRC thanh cong: set output va enabled `COPY CRC`.
- Them `copy_crc_result()` copy noi dung `txt_crc_output` vao clipboard.
- Refresh theme cho button moi.

## Verification
Theo yeu cau cua user: khong chay test va khong runtime check. Chi doc lai code lien quan de xac nhan trang thai khoi tao cua `COPY CRC` la disabled.
