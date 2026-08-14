V-CODE v2.0.1 - EEIV Diagnostic Tool
AES EEIV by DAT TRAN

============================================================
1. Introduction
============================================================
V-CODE is a Windows desktop application for vehicle diagnostic log analysis, ECU configuration management, coding value review, CRC calculation, and data conversion.

Main tabs:
- Log Analyzer: Load diagnostic logs, analyze UDS/CAN messages, filter data, copy results, and export reports.
- Coding value: Import coding definitions from Excel/JSON, encode payloads, edit raw/decoded values, compare before/after data, transfer CRC values, and export reports.
- CRC_Converter: Calculate CRC8_SAE_J1850, convert data between common formats, and generate QR codes.
- Vehicle Manager: Manage vehicle packages, ECU lists, request/response IDs, resources, shortcuts, and import/export ECU data.
- License & Support: Display support information, QR support image, and contact details.

============================================================
2. System Requirements
============================================================
Release package:
- Windows 10/11 x64.
- No Python installation is required.
- Keep all runtime folders in the extracted release directory.

Source code:
- Python 3.x.
- Dependencies listed in requirements.txt.
- Valid license files in the license/ directory.

============================================================
3. Running the Release Version
============================================================
1. Extract the full ZIP/release package.
2. Do not move the EXE file out of the extracted folder.
3. Make sure these folders stay beside the EXE:
   - config
   - license
   - shortcuts
   - output
4. Run the application EXE.
5. If the license is missing, invalid, or expired, the app will start in Limited Mode.

============================================================
4. Running from Source Code
============================================================
1. Create and activate a virtual environment:

   python -m venv .venv
   .venv\Scripts\activate

2. Install dependencies:

   pip install -r requirements.txt

3. Run the application:

   python main.py

Note: The application validates the license at startup. Required license files must be available in the license/ folder.

============================================================
5. Important Directory Structure
============================================================
config/
- vehicles/: Vehicle packages and ECU configuration data.
- quick_filters.json: Quick filter configuration for Log Analyzer.
- display_names.json: Display name and display rule mapping.
- uds_services.json, uds_user.json: UDS service definitions and user-defined service rules.
- export_coding_files/: JSON coding definition files exported from Excel for reuse.
- Coding/: Default folder for Excel coding files.

license/
- License files, public key, and license validation resources.

shortcuts/
- shortcuts.json: Keyboard shortcut configuration. Shortcuts are active only in the Log Analyzer tab.

output/
- Report_LogAnalyzer/: Exported reports from Log Analyzer.
- Report_CodingValue/: Exported reports from Coding value.

report/
- Legacy report folder. Current versions export reports under output/.

gui/resources/images/
- Runtime images and icons, including support.qr.jpg for the License & Support tab.

============================================================
6. Log Analyzer
============================================================
Main features:
- Select vehicle package and log file.
- Analyze CAN/UDS diagnostic logs.
- Search/filter messages by keyword or key data.
- Use Quick Filter presets.
- Import/export filters.
- Copy analyzed results.
- Export reports to output/Report_LogAnalyzer/<date>/.

Notes:
- Select a valid vehicle and log file before analyzing.
- Switching Quick Filter clears previous table selections.
- Keyboard shortcuts are active only while the Log Analyzer tab is active.

============================================================
7. Coding value
============================================================
Main features:
- Browse Excel coding files from config/Coding.
- Import Excel coding definitions into JSON files under config/export_coding_files/.
- Select coding JSON from the dropdown and load table data without re-importing Excel.
- Read only Excel columns whose headers start with $, for example:
  $Parameter
  $BytePos (from 0)
  $BitPos
  $BitLength
  $MethodType
- Encode payload data into Raw value cells based on Byte Pos, Bit Pos, and Bit Length.
- Edit Raw value or Decoded Value (Editable), with synchronized decoded/raw display.
- Support bit-field decoding, for example one byte can contain multiple 4-bit values.
- Preview the current payload and highlight bytes changed by table edits.
- CHECK to create comparison columns:
  Raw value (before)
  Decoded value (before)
  Result
- Result status uses MATCH or No-M.
- Working log shows Total No-M, changed bytes, before/after decoded values, and CRC change.
- COPY concatenates Raw value cells into a payload string formatted as XX XX XX.
- EXPORT opens a save dialog and exports the visible table to Excel under output/Report_CodingValue/<date>/.
- No-M rows are highlighted with warning formatting in exported Excel reports.
- Parameter filter supports searching Parameter and Result values.
- No-M filter and Refresh filter buttons are available above the table.
- CRC values can be received from the CRC_Converter tab through Transfer CRC.

MethodType format:
- Both = and : delimiters are accepted.
- Examples:
  0x0=Unsupported
  0x1: Brahminy White
  0x2: De Sat Silver

============================================================
8. CRC_Converter
============================================================
CRC8_SAE_J1850:
- Calculate CRC from HEX byte input.
- Accepts spaces and newlines.
- Accepts upper/lowercase HEX.
- Invalid input is rejected without crashing the app.
- COPY CRC copies the calculated CRC value.
- Transfer CRC sends the calculated CRC to the CRC row in Coding value.
- COPY CRC and Transfer CRC are disabled while the CRC output is empty.

CRC parameters:
- poly = 0x1D
- init = 0xFF
- refin = False
- refout = False
- xorout = 0xFF

Converter:
- Convert data between:
  Hexadecimal
  Decimal
  ASCII
  Binary
  TXT
  Octa
- From and To formats must be different.
- Supported examples:
  HEX to DEC:   41 42 43 -> 65 66 67
  HEX to ASCII: 41 42 43 -> ABC
  DEC to HEX:   65 66 67 -> 41 42 43
  ASCII to HEX: ABC -> 41 42 43

QR Code Generator:
- Generate a QR code from text input.
- Preview the QR image in the tab.
- Copy QR image to clipboard.
- Clear QR input and preview.

============================================================
9. Vehicle Manager
============================================================
Main features:
- Create/delete vehicle packages.
- Add/delete/edit ECUs.
- Import ECU list.
- Export selected vehicle ECU list.
- Import Display Names JSON.
- Import Rules Display Names.
- Configure keyboard shortcuts.

Notes:
- Click Save after editing vehicle/ECU data.
- Renaming an ECU saves the new name while preserving unchanged request/response IDs.
- Duplicate request/response IDs are checked only when those IDs are actually changed.

============================================================
10. License & Support
============================================================
The License & Support tab displays:
- Development support message.
- Support QR image.
- Contact email:
  tranducdat.eng@gmail.com | tranducdatks95@gmail.com
- Phone:
  0329000529

============================================================
11. Build Release
============================================================
build_release.py prepares the release output under:

dist/EEIV Diagnostic/

Copied/created release items include:
- config
- license
- shortcuts
- output
- output/Report_LogAnalyzer
- output/Report_CodingValue
- README.txt

============================================================
12. Troubleshooting
============================================================
Limited Mode
- The app can still open without a valid license.
- CRC_Converter and License & Support remain available.
- Check that the license/ folder exists.
- Check that the license file and public key are present.
- Check that the license is still valid.

Cannot Find Exported Reports
- Check output/Report_LogAnalyzer or output/Report_CodingValue.
- If an Excel report file is open, close it and export again.

Failed to Load Coding JSON
- Check the selected JSON file in config/export_coding_files/.
- If the JSON is invalid, import it again from the original Excel coding file.

Coding Table Is Empty After Import
- Confirm that the Excel sheet contains supported $ columns.
- Confirm that Byte Pos, Bit Pos, Bit Length, Parameter, and MethodType columns are present.

CRC Transfer Does Nothing
- Calculate CRC first.
- Transfer CRC is disabled when CRC output is empty.
- Ensure the Coding value table has a CRC parameter row loaded.

Support QR Code Is Not Displayed
- Check gui/resources/images/support.qr.jpg.
- If missing, the app may fall back to support_qr.jpg.

============================================================
13. Developer / Contact
============================================================
Name: DAT TRAN - AES Company
Email: tranducdat.eng@gmail.com | tranducdatks95@gmail.com
Phone: 0329000529
