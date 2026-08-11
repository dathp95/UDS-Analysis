# Fix Coding Value Combobox Options

## Request
- Combobox trong tab Coding value bi hien thi de len nhau.
- Gia tri Excel o cot `$MethodType` tai byte 14 co nhieu dong, moi dong phai thanh mot option rieng trong combobox.

## Changes
- Giu combobox cua bang Coding value o kich thuoc on dinh va tang row height de khong bi de len nhau.
- Tat sorting cho bang co cell widget de tranh widget editor bi gan sai row khi render.
- Bo sung test parser Excel de dam bao chuoi multi-line `0x...=...` duoc tach thanh tung option rieng.
- Bo sung test UI table de dam bao combobox co tung item rieng va row height du cho combo.

## Verification
- `python -m unittest tests.core.test_coding_value_excel`
- `python -m unittest tests.gui.test_coding_value_tab`
- `python -m unittest tests.core.test_coding_value_excel tests.gui.test_coding_value_tab tests.gui.test_main_window_shortcuts`
- `python -m py_compile core/coding_value.py gui/widgets/coding_value/coding_value_table.py tests/core/test_coding_value_excel.py tests/gui/test_coding_value_tab.py`
- Kiem tra truc tiep file `config/Coding/MHU CDS Coding.xlsx`: `$MethodType` duoc tach thanh 12 option rieng: Unsupported, Comfort, Premium, Earth, Wind, Sky, HerioGreen, Reserved, Reserved, Reserved, Reserved, Invalid.

## Known Environment Note
- `python -m unittest discover` van loi do thieu dependency moi truong: `cryptography` va `can`.
