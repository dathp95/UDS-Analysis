V-CODE v1.0.2 - EEIV Diagnostic Tool
AES EEIV by DAT TRAN

============================================================
1. Gioi thieu
============================================================
V-CODE la cong cu desktop ho tro doc, phan tich va xuat bao cao log chan doan xe. Ung dung co cac tab chinh:

- Log Analyzer: doc log, phan tich UDS/CAN, loc nhanh, copy/export ket qua.
- Coding value: import du lieu coding tu Excel/JSON, encode payload, so sanh before/after, export report.
- Vehicle Manager: quan ly vehicle package, ECU list, request/response ID, resource va import/export ECU list.
- License & Support: hien thi thong tin support, QR support va thong tin lien he.

============================================================
2. Yeu cau he thong
============================================================
- Windows 10/11 x64.
- Neu chay ban release: khong can cai Python.
- Neu chay source code: can Python va cac package trong requirements.txt.

============================================================
3. Huong dan chay ban release
============================================================
1. Giai nen toan bo file ZIP/release package.
2. Khong di chuyen file EXE ra khoi thu muc da giai nen.
3. Dam bao cac thu muc runtime nam cung package:
   - config
   - license
   - shortcuts
   - output
4. Chay file EXE cua ung dung.
5. Neu license khong hop le hoac het han, app se hien thong bao License Error.

============================================================
4. Huong dan chay source code
============================================================
1. Tao va kich hoat virtual environment:

   python -m venv .venv
   .venv\Scripts\activate

2. Cai dependencies:

   pip install -r requirements.txt

3. Chay ung dung:

   python main.py

Luu y: app se validate license khi khoi dong. File license can nam trong thu muc license.

============================================================
5. Cau truc thu muc quan trong
============================================================
config/
- vehicles/: du lieu vehicle package va ECU.
- quick_filters.json: cau hinh quick filter cua Log Analyzer.
- display_names.json: mapping display name/rule hien thi.
- uds_services.json, uds_user.json: cau hinh UDS service/user-defined service.
- export_coding_files/: JSON duoc export tu file Excel coding de tai su dung.
- Coding/: thu muc de dat file Excel coding.

license/
- Chua file license va public key/cau hinh license can thiet cho app.

shortcuts/
- shortcuts.json: cau hinh phim tat. Shortcut chi kich hoat trong tab Log Analyzer.

output/
- Report_LogAnalyzer/: report export tu tab Log Analyzer.
- Report_CodingValue/: report export tu tab Coding value.

report/
- Thu muc cu, khong phai output chinh cua cac version hien tai.

gui/resources/images/
- Anh/icon runtime, bao gom QR support neu co.

============================================================
6. Log Analyzer
============================================================
Chuc nang chinh:
- Chon vehicle va file log.
- Analyze log CAN/UDS.
- Filter/search theo keyword.
- Quick filter: tao, clone, edit, delete, import/export filters.
- Copy ket qua dang ASC/text.
- Export report vao output/Report_LogAnalyzer/<date>/.

Luu y:
- Can chon vehicle va log hop le truoc khi analyze.
- Quick filter se clear selection cu khi doi filter.
- Shortcut chi co tac dung khi dang o tab Log Analyzer.

============================================================
7. Vehicle Manager
============================================================
Chuc nang chinh:
- Tao/xoa vehicle package.
- Them/xoa/sua ECU.
- Import ECU list.
- Export vehicle ECU list.
- Import Display Names JSON.
- Import Rules Display Names.
- Cau hinh keyboard shortcuts.

Luu y:
- Sau khi sua ECU, bam Save de luu thay doi.
- Khi doi ten ECU, app se kiem tra trung ten va giu nguyen request/response ID neu khong thay doi.

============================================================
8. Coding value
============================================================
Chuc nang chinh:
- Browse file Excel coding trong config/Coding.
- Import Excel thanh JSON trong config/export_coding_files.
- Chon JSON tu dropdown de load table ma khong can import Excel lai.
- Encode payload vao Raw value theo Byte Pos/Bit Pos/Bit Length.
- Sua Raw value hoac Decoded Value (Editable), dong bo preview payload.
- CHECK de tao cot Raw value (before), Decoded value (before), Result.
- Working log hien thi cac byte thay doi va CRC before/after.
- COPY ghep Raw value thanh chuoi xx xx xx.
- EXPORT table hien tai ra Excel vao output/Report_CodingValue/<date>/.

Format Excel coding:
- App uu tien cac cot co dau $ o dau ten cot, vi du:
  $Parameter
  $BytePos (from 0)
  $BitPos
  $BitLength
  $MethodType

Format MethodType:
- Chap nhan dau = hoac :
  0x0=Unsupported
  0x1: Brahminy White
  0x2: De Sat Silver

============================================================
9. License & Support
============================================================
Tab License & Support hien thi:
- Noi dung support development.
- QR support image.
- Email lien he:
  tranducdat.eng@gmail.com | tranducdatks95@gmail.com
- Phone:
  0329000529

============================================================
10. Build release
============================================================
Script build_release.py copy cac thu muc runtime vao:

dist/EEIV Diagnostic/

Cac thu muc duoc copy/tao:
- config
- license
- shortcuts
- output
- output/Report_LogAnalyzer
- output/Report_CodingValue
- README.txt

============================================================
11. Troubleshooting
============================================================
License Error
- Kiem tra thu muc license co ton tai va dung file license.
- Kiem tra license con han su dung.

Khong thay report export
- Kiem tra output/Report_LogAnalyzer hoac output/Report_CodingValue.
- Dong file Excel report neu dang mo roi export lai.

Khong load duoc Coding JSON
- Kiem tra file JSON trong config/export_coding_files.
- Neu JSON loi, import lai tu file Excel coding goc.

Khong hien QR support
- Kiem tra file anh trong gui/resources/images.
- App uu tien support.qr.jpg, neu khong co se dung support_qr.jpg.

============================================================
12. Developer / Contact
============================================================
Name: DAT TRAN - AES Company
Email: tranducdat.eng@gmail.com | tranducdatks95@gmail.com
Phone: 0329000529
