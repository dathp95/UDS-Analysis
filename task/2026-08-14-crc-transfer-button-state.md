# CRC Transfer Button State

Date: 2026-08-14

## Request
Disable the `Transfer CRC` button in the `CRC_Converter` tab when the CRC output field has no value.

## Changes
- Initialized `btn_transfer_crc` as disabled.
- Added `_update_crc_button_states()` to keep `COPY CRC` and `Transfer CRC` in sync with `txt_crc_output`.
- Connected `txt_crc_output.textChanged` to update button states automatically.
- Updated CRC converter UI tests for initial disabled state, enabled state after calculation, and disabled state after invalid input clears CRC output.

## Verification
- `python -m unittest tests.gui.test_crc_converter_tab` passed: 16 tests.
- `python -m py_compile gui\tabs\crc_converter_tab.py tests\gui\test_crc_converter_tab.py` passed.
