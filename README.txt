V-CODE v3.0.6
EEIV Diagnostic Tool
AES EEIV by DAT TRAN

============================================================
1. INTRODUCTION
============================================================

V-CODE is an automotive engineering tool for diagnostic log,
Coding Value, and vehicle Sleep Current analysis.

Main features:
- CAN/UDS diagnostic log analysis.
- ECU Request/Response search and filtering.
- Coding Value analysis and comparison.
- CRC calculation and data conversion.
- Q Current / Sleep Current analysis.
- Vehicle and ECU management.
- Excel report generation.


============================================================
2. LOG ANALYZER
============================================================

Used to analyze CAN/UDS diagnostic logs.

Features:
- Read ASC/BLF log files.
- Select Vehicle and Log Channel.
- Analyze UDS Request/Response transactions.
- Identify ECU from Request/Response IDs.
- Display Response Time and transaction status.
- Search analyzed data.
- Create and use Quick Filters.
- Copy Request / Response / Transaction.
- Export Excel reports.


============================================================
3. CODING VALUE
============================================================

Used to read, edit, and verify ECU Coding Values.

Features:
- Multiple independent Coding Panels.
- Load Coding Definitions.
- Decode Raw Values into readable values.
- Edit Raw Value or Decoded Value.
- Preview payload.
- Highlight changed data.
- Compare Before / After values.
- Display MATCH / No-M results.
- Search and filter Parameters.
- Receive CRC from CRC_Converter.
- Copy payload.
- Export Excel reports.


============================================================
4. CRC_CONVERTER
============================================================

Provides quick data processing tools.

CRC:
- Calculate CRC8_SAE_J1850.
- Copy CRC.
- Transfer CRC to Coding Value.

Converter:
- HEX
- Decimal
- ASCII
- Binary
- TXT
- Octa

QR Code:
- Generate QR Code from text.
- Preview and Copy QR Code.


============================================================
5. Q CURRENT
============================================================

Used to analyze vehicle Sleep Current.

Features:
- Import CSV/XLSX data.
- Save and reload imported datasets.
- Configure Standard Current.
- Configure Wake Up Limit.
- Configure Wake Duration.
- Select the analysis time range.
- Configure Sampling Duration.

Current Chart:
- Zoom and Scroll.
- Fit All.
- Pin.
- Cursor A/B.
- Delta Time / Delta Current measurement.
- Capture.
- Invert Y Axis.
- Sleep Limit display.
- Wake-up Event highlighting.

Analysis results:
- PASSED / FAILED.
- Average Sleep Current.
- Minimum Current.
- Maximum Current.
- Wake-up Events.
- Start / End Time.
- Duration.
- Total Samples.
- Sample Interval.

Excel reports can include the source data, analysis results,
and Current Chart.


============================================================
6. VEHICLE MANAGER
============================================================

Used to manage Vehicle and ECU configurations.

Features:
- Create / Delete Vehicle.
- Add / Delete ECU.
- Edit ECU information.
- Manage Request ID / Response ID.
- Import ECU List.
- Export Vehicle.
- Import Display Names.
- Import Rules Display Names.
- Configure Keyboard Shortcuts.


============================================================
7. LICENSE & SUPPORT
============================================================

V-CODE uses a license system to manage feature access.

Valid license:
- Licensed features operate normally.

Invalid or expired license:
- V-CODE starts in Limited Mode.

Support:

Email:
tranducdat.eng@gmail.com
tranducdatks95@gmail.com

Phone:
0329000529


============================================================
8. REPORTS
============================================================

Reports are stored in:

output/Report_LogAnalyzer/

output/Report_CodingValue/

output/Report_QCurrent/

If a report cannot be exported:
- Check whether the existing Excel file is open.
- Close the Excel file and try exporting again.


============================================================
9. VERSION INFORMATION
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