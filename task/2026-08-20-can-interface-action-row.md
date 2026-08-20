# CAN Interface Action Row

## Summary

- Adjusted the `CAN Interface` action area so `Refresh`, `Connect`, `Disconnect`, and the connection status label share the same horizontal row.
- Stored the row as `self.action_layout` to make the layout explicit and testable.
- Vertically aligned all action widgets and set the status label height to match the button row.
- Restored button-state logic to also respect the real service connection state.
- Added a GUI unit test to verify the three buttons and status label stay in the same row.

## Verification

- `python -m py_compile gui\tabs\can_interface_tab.py tests\gui\test_can_interface_tab.py`
- `python -m unittest tests.gui.test_can_interface_tab`
