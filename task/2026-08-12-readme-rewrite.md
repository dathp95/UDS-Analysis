# README rewrite

## Yeu cau
Viet lai file `README.txt` cho app hien tai.

## Thay doi
- Viet lai README theo format plain text, tieng Viet khong dau de tranh loi encoding trong release Windows.
- Bo sung gioi thieu V-CODE v1.0.2 va cac tab: Log Analyzer, Coding value, Vehicle Manager, License & Support.
- Bo sung huong dan chay release va source code.
- Cap nhat cau truc folder config/license/shortcuts/output.
- Cap nhat output moi: `output/Report_LogAnalyzer` va `output/Report_CodingValue`.
- Bo sung ghi chu build release, troubleshooting va contact.

## Verification
- `Get-Content README.txt -TotalCount 80`
- `rg -n "Gioi thieu|Log Analyzer|Vehicle Manager|Coding value|License & Support|Report_LogAnalyzer|Report_CodingValue|Giá|Ã|EMAL" README.txt`
- Python validation kiem tra cac noi dung chinh co trong README.
