V-CODE v1.0.2 - EEIV Diagnostic Tool
AES EEIV by DAT TRAN

============================================================
1. Introduction
============================================================
V-CODE is a desktop tool supporting reading, analyzing, and exporting vehicle diagnostic logs. The application consists of the following main tabs:

- Log Analyzer: Read logs, analyze UDS/CAN, quick filter, copy/export results.
- Coding value: Import coding data from Excel/JSON, encode payload, compare before/after, export reports.
- Vehicle Manager: Manage vehicle packages, ECU lists, request/response IDs, resources, and import/export ECU lists.
- License & Support: Display support information, support QR code, and contact info.

============================================================
2. System Requirements
============================================================
- Windows 10/11 x64.
- Running the release version: No Python installation required.
- Running from source code: Python and packages listed in requirements.txt are required.

============================================================
3. Instructions for Running Release Version
============================================================
1. Extract all contents of the ZIP / release package.
2. Do not move the EXE file out of the extracted folder.
3. Ensure the following runtime folders are located in the same directory:
   - config
   - license
   - shortcuts
   - output
4. Run the application's EXE file.
5. If the license is invalid or expired, the app will display a License Error message.

============================================================
4. Instructions for Running Source Code
============================================================
1. Create and activate a virtual environment:

   python -m venv .venv
   .venv\Scripts\activate

2. Install dependencies:

   pip install -r requirements.txt

3. Run the application:

   python main.py

Note: The app validates the license upon startup. The license file must be placed inside the license/ folder.

============================================================
5. Important Directory Structure
============================================================
config/
- vehicles/: Vehicle package data and ECUs.
- quick_filters.json: Quick filter configuration for Log Analyzer.
- display_names.json: Display name mapping / display rules.
- uds_services.json, uds_user.json: UDS service and user-defined service configurations.
- export_coding_files/: JSON files exported from Excel coding files for reusability.
- Coding/: Directory designated for Excel coding files.

license/
- Contains license files, public key, and required license configuration for the app.

shortcuts/
- shortcuts.json: Keyboard shortcut configuration. Shortcuts are active only within the Log Analyzer tab.

output/
- Report_LogAnalyzer/: Reports exported from the Log Analyzer tab.
- Report_CodingValue/: Reports exported from the Coding value tab.

report/
- Legacy directory; not the primary output location for current versions.

gui/resources/images/
- Runtime images/icons, including the support QR code if available.

============================================================
6. Log Analyzer
============================================================
Main Features:
- Select vehicle and log file.
- Analyze CAN/UDS logs.
- Filter/search by keyword.
- Quick filter: Create, clone, edit, delete, import/export filters.
- Copy results in ASC/text format.
- Export reports to output/Report_LogAnalyzer/<date>/.

Notes:
- A valid vehicle and log file must be selected before analyzing.
- Quick filter will clear previous selections when switching filters.
- Shortcuts are functional only while active in the Log Analyzer tab.

============================================================
7. Vehicle Manager
============================================================
Main Features:
- Create/delete vehicle packages.
- Add/delete/edit ECUs.
- Import ECU list.
- Export vehicle ECU list.
- Import Display Names JSON.
- Import Rules Display Names.
- Configure keyboard shortcuts.

Notes:
- After editing an ECU, click Save to apply changes.
- When renaming an ECU, the app checks for duplicate names and preserves the request/response IDs if unchanged.

============================================================
8. Coding value
============================================================
Main Features:
- Browse Excel coding files in config/Coding.
- Import Excel to JSON in config/export_coding_files.
- Select JSON from dropdown to load table without re-importing Excel.
- Encode payload into Raw value based on Byte Pos/Bit Pos/Bit Length.
- Edit Raw value or Decoded Value (Editable), synchronizing payload preview.
- CHECK to generate Raw value (before), Decoded value (before), and Result columns.
- Working log displays modified bytes and CRC before/after.
- COPY to concatenate Raw values into a string formatted as xx xx xx.
- EXPORT current table to Excel into output/Report_CodingValue/<date>/.

Excel Coding Format:
- The app prioritizes columns starting with $ at the beginning of the column name, e.g.:
  $Parameter
  $BytePos (from 0)
  $BitPos
  $BitLength
  $MethodType

MethodType Format:
- Accepts = or : delimiter:
  0x0=Unsupported
  0x1: Brahminy White
  0x2: De Sat Silver

============================================================
9. License & Support
============================================================
The License & Support tab displays:
- Development support message.
- Support QR code image.
- Contact email:
  tranducdat.eng@gmail.com | tranducdatks95@gmail.com
- Phone:
  0329000529

============================================================
10. Build Release
============================================================
The build_release.py script copies runtime folders into:

dist/EEIV Diagnostic/

Folders copied/created:
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
- Verify that the license folder exists and contains the correct license file.
- Check if the license is still valid and not expired.

Cannot Find Exported Reports
- Check output/Report_LogAnalyzer or output/Report_CodingValue.
- Close the Excel report file if it is currently open, then export again.

Failed to Load Coding JSON
- Verify the JSON file in config/export_coding_files.
- If the JSON file is invalid, re-import it from the original Excel coding file.

Support QR Code Not Displayed
- Check image files in gui/resources/images.
- The app prioritizes support.qr.jpg; if absent, it falls back to support_qr.jpg.

============================================================
12. Developer / Contact
============================================================
Name: DAT TRAN - AES Company
Email: tranducdat.eng@gmail.com | tranducdatks95@gmail.com
Phone: 0329000529