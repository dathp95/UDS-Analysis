# Batch QR Code Excel Export V1

## Scope

Implemented the latest V1 specification, superseding the earlier background-export
request: synchronous export, 1-50 codes, at most 24 codes per sheet, no worker,
QThread, progress bar, CSV import or database storage. No commit or push was made.

## Changed Files

- `core/qr_excel_export.py`: Qt-free validation, layout and atomic workbook export.
- `gui/dialogs/qr_list_dialog.py`: input/count/limit warning, save dialog, export,
  error handling and Light/Dark styling.
- `gui/tabs/crc_converter_tab.py`: button immediately after Clear QR, modal dialog
  launch/cleanup and theme forwarding. Existing single-QR and CRC logic unchanged.
- `tests/core/test_qr_excel_export.py`: workbook, payload and failure-path tests.
- `tests/gui/test_qr_list_dialog.py`: dialog and integration tests.
- This report.

## Behavior

Blank lines are ignored, outer whitespace trimmed, internal whitespace, leading
zeros, Unicode, duplicates and ordering preserved. The dialog shows the complete
count and an inline warning above 50; it does not truncate input. The core repeats
validation before generating any images, including rejecting unsafe XML strings.

The existing `generate_qr_png_bytes()` is reused unchanged. Native PNG data stays
in memory until workbook saving completes. Each image is anchored at approximately
135 x 135 pixels, centered in one of three columns. Text is stored immediately
below it, explicitly as string data with text number format, including formula-like
and Excel error-like values. Formula prefixes do not change the encoded QR content.

Sheets are named QR_001, QR_002, etc., have no title rows or blank sheets, and use
hidden gridlines, A4 portrait, and one-page-wide/one-page-high fit settings.
Layout uses openpyxl's [image embedding](https://openpyxl.readthedocs.io/en/stable/images.html)
and [print settings](https://openpyxl.readthedocs.io/en/stable/print_settings.html).

A unique temporary workbook is created beside the selected destination. Only a
successful save is followed by atomic replacement. All owned image streams,
workbook resources, output handles and temporary files are cleaned up after
success or error. Existing destinations survive generation/save/replace failures.

Cancel closes the idle dialog. Cancelling file selection creates nothing. While
synchronous export runs, editing/export/cancel controls are disabled and a guard
prevents reentry. There is no mid-export cancellation mechanism in V1.

## Validation

Command:

`python -m unittest tests.core.test_qr_excel_export tests.core.test_qr_generator tests.core.test_crc tests.core.test_converter tests.gui.test_qr_list_dialog tests.gui.test_crc_converter_tab -q`

Result: 51 tests passed. Includes 1/3/24/25/48/50-code workbook boundaries, rejection
of 0/51 codes before image generation, blank lines, duplicate/leading-zero/Unicode
values, formula-like strings, image anchors/order, valid ZIP packages, successful
openpyxl reopening, partial-save cleanup, destination preservation, buffer cleanup,
GUI limit bypass prevention, filename/extension, cancellation, reentry, themes and
existing CRC/converter/single-QR behavior.

Embedded image pixels were compared against the existing generator for each
corresponding normalized string. No independent QR decoder is installed, so this
is not a claim of independent scanner or physical-print validation.

A practical export of 50 synthetic VIN-shaped codes produced three sheets and a
39,965-byte workbook in 0.472 seconds on this machine. This is an observation,
not a latency guarantee.

Qt offscreen rendered both dialog themes at 520 x 450. The QR action row had no
overlapping buttons at a 1408 x 850 resulting tab size. The offscreen environment
has no working font families, so glyph appearance was not visually certified.
Python syntax and git whitespace checks passed.

## Dependencies and Limits

Existing dependencies suffice: Python 3.12, PySide6 6.11.1, openpyxl 3.1.5,
Pillow 12.3.0 and qrcode 8.2 in the validation environment. `qrcode[pil]` already
supplies Pillow through requirements.txt. No dependency or packaging edits made.

- Export is synchronous and can briefly block the dialog, especially on slow disks.
- QR capacity limits still apply; oversized payloads fail without publishing a file.
- Very long/dense values can reduce printed readability when fitting A4. Actual
  scanner, font and printer checks remain necessary for those cases.
- Excel desktop opening/print preview and a packaged EXE build were not executed.

Suggested commit: `CRC Converter - Batch QR Excel Export V1`
