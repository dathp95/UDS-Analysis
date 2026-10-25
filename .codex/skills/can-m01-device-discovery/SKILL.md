# V-CODE CAN Interface — Milestone 01: Vector Device Discovery

## Role

You are a senior Automotive Software Engineer specializing in:

- Python 3.12
- PySide6 desktop applications
- Vector XL Driver API
- python-can
- Automotive CAN / CAN FD networks
- Software testing and hardware abstraction

Project: V-CODE

Repository: `dathp95/UDS-Analysis`

Reference repository: `dathp95/CBT`

Implement Milestone 01 only.

Do not implement features belonging to later milestones.

## 1. Objective

Replace hardcoded Vector device and CAN channel lists with actual hardware discovery.

The user should be able to:

1. Connect a Vector interface to Windows.
2. Open the CAN Interface tab.
3. Click Refresh.
4. See detected Vector devices.
5. Select a device.
6. See the available CAN channels of that device.
7. Select an available channel.
8. Keep the existing bitrate selection and Connect/Disconnect functionality.

Do not automatically connect to a CAN bus during Refresh.

## 2. Required Source Review

Before editing, read the latest versions of:

- `gui/tabs/can_interface_tab.py`
- `services/can/can_service.py`
- `services/can/vector_backend.py`
- `services/can/can_config.py`
- `services/can/__init__.py`
- `tests/services/test_can_service.py`
- `tests/gui/test_can_interface_tab.py`
- `requirements.txt`

Also inspect existing threading patterns, theme controls and application shutdown handling.

Review the Vector XL Driver documentation where accessible:

- `docs/can_interface/XL_Driver_Library_Manual_EN.pdf`
- `can_interface/XL_Driver_Library_Manual_EN.pdf`
- `CBT/reference_docs/XL_Driver_Library_Manual_EN.pdf`

These are reference materials, not permission to rewrite the existing architecture.

Do not claim to have verified content that could not be read.

## 3. Existing Architecture

Preserve:

```text
CANInterfaceTab
      |
      v
  CANService
      |
      v
 VectorBackend
      |
      v
  python-can
      |
      v
 Vector XL Driver
```

Existing connection functionality must remain compatible.

Do not directly access hardware from the GUI.

Do not move business logic into the GUI.

## 4. Discovery API

Investigate and use the installed version of python-can.

Preferred discovery API, when supported:

```python
can.detect_available_configs(
    interfaces=["vector"]
)
```

Inspect the actual return schema and python-can version before implementation.

For Vector channels, useful metadata can include:

- interface
- channel
- serial
- channel_index
- hw_type
- hw_index
- hw_channel
- supports_fd

Do not assume every field is always present.

Do not assume channel indices restart at zero for each device.

Do not assume the device model uniquely identifies a physical interface.

If multiple physical Vector devices are connected, keep them distinguishable using stable hardware metadata such as serial number and hardware identifiers.

Device model names should come from driver-supported metadata where available.

Do not fabricate model names from arbitrary hardware type numbers.

When the actual model is unknown, display a neutral name such as `Vector Device` along with identifying metadata.

## 5. New Data Models

Create a small, typed hardware discovery model, preferably in:

`services/can/can_device.py`

Suggested immutable dataclasses:

```python
@dataclass(frozen=True)
class CANChannelInfo:
    channel: int
    channel_index: int | None
    name: str
    supports_fd: bool
    hw_channel: int | None = None


@dataclass(frozen=True)
class CANDeviceInfo:
    name: str
    serial: int | None
    hw_type: int | None
    hw_index: int | None
    channels: tuple[CANChannelInfo, ...]
```

You may refine these models to match the installed python-can API.

Important requirements:

- Preserve an unambiguous mapping from GUI selection to backend connection parameters.
- Do not lose `channel_index` or `serial`.
- Avoid mutable dictionaries as the public API between GUI and service.
- Use stable identifiers for multiple connected devices.
- Preserve necessary original discovery metadata through typed fields.
- If hardware identity cannot be determined reliably, avoid merging unrelated devices.

## 6. VectorBackend

Update:

`services/can/vector_backend.py`

Implement:

```python
def fn_refresh(self):
    ...
```

Responsibilities:

- Load python-can safely.
- Query available Vector CAN interfaces.
- Normalize discovery results into typed device/channel models.
- Return discovered devices to CANService.
- Never open a CAN bus during discovery.
- Never change the active connection as a side effect of Refresh.

Handle separately:

1. python-can missing.
2. Vector XL Driver unavailable.
3. Driver available but no Vector hardware found.
4. Hardware detected but no CAN-capable channels.
5. Unexpected discovery error.

Do not silently turn every exception into an empty list.

Do not use hardcoded VN1630A/VN1640A channel mappings.

Do not add custom ctypes bindings when the installed python-can API already provides sufficient discovery support.

## 7. CANService

Update:

`services/can/can_service.py`

The service must provide a clear discovery result to the GUI.

Requirements:

- Delegate hardware detection to VectorBackend.
- Validate normalized discovery results.
- Keep discovery independent from connection.
- Preserve existing Connect/Disconnect behavior.
- Support dependency injection for tests.
- Do not introduce global mutable state.

If no hardware is connected, return an explicit empty device collection.

If the driver is unavailable, raise a clear typed exception or return a structured error that distinguishes this condition from no hardware.

## 8. GUI Requirements

Update:

`gui/tabs/can_interface_tab.py`

Replace the hardcoded device and channel population with dynamic hardware discovery.

### Device ComboBox

Display detected devices.

Example:

`VN1630A - SN 123456`

If the model cannot be identified:

`Vector Device - SN 123456`

Do not display invented or unsupported hardware names.

### Channel ComboBox

Populate channels belonging only to the selected device.

Example:

```text
CAN 1
CAN 2
```

Keep the original channel number and global channel index internally.

Display only CAN-capable channels.

Do not display unsupported LIN channels as CAN channels.

### Refresh button

When clicked:

1. Request discovery.
2. Read the returned device collection.
3. Populate Device ComboBox.
4. Populate Channel ComboBox according to the selected device.
5. Update status and control availability.

If multiple devices are found, preserve the previous selection when the same device and channel remain available.

If hardware disappears, clear stale disconnected selections.

If discovery reports no devices, the UI must not offer a fake device for connection.

### Connected behavior

Milestone 01 must not disrupt an existing active connection.

Disable Refresh while connected, or use a clearly defined safe strategy that does not replace active connection settings.

Do not silently disconnect a running session.

### Button states

When no device/channel is available:

- Refresh: enabled
- Connect: disabled
- Disconnect: disabled

When a valid device/channel is selected and disconnected:

- Refresh: enabled
- Connect: enabled
- Disconnect: disabled

When connected:

- Connect: disabled
- Disconnect: enabled
- Refresh: disabled unless safely supported

Preserve existing Light/Dark theme support.

## 9. Backward Compatibility

Preserve the existing public CANConfig usage wherever possible:

```python
CANConfig(
    interface="vector",
    channel=0,
    bitrate=500000,
)
```

Existing unit tests and external callers should continue working.

Do not add mandatory constructor fields that break existing code.

If additional connection metadata is needed later, introduce optional typed fields with safe defaults and test compatibility.

Do not claim that the detected device selection controls connection until its metadata is actually passed to the backend.

If complete selection-to-connection mapping must wait until Milestone 02, keep Connect disabled for selections that cannot be mapped correctly and document the limitation.

Prefer a small compatible fix over a broad refactor.

## 10. Responsiveness

Hardware discovery may block.

Investigate whether the project has an established worker/thread pattern.

Implement discovery away from the GUI thread when practical and necessary for responsive behavior.

Requirements if threading is introduced:

- Worker must not modify widgets.
- Signals must update GUI on the main thread.
- Prevent duplicate Refresh operations.
- Do not terminate an active QThread forcibly.
- Ensure thread cleanup during tab/application shutdown.
- Ignore stale results safely.
- Avoid changing connection state from the worker.

Do not introduce threading just for decoration.

## 11. Error Handling

Provide meaningful messages:

### Missing python-can

`python-can is not installed.`

### Missing Vector Driver

`Vector XL Driver is unavailable.`

### No hardware

`No Vector CAN device detected.`

### No CAN channel

`The detected Vector device has no available CAN channel.`

### Unexpected error

Show a concise user-facing message and retain technical details for debugging.

Do not claim a driver is absent solely because no devices were returned.

## 12. Unit Tests

Update existing tests rather than deleting them.

Use FakeCANBackend or mocked python-can responses.

Test:

1. No hardware connected.
2. One device with one CAN channel.
3. One device with multiple CAN channels.
4. Multiple devices.
5. Device without CAN-capable channels.
6. Missing python-can.
7. Missing Vector driver.
8. Unexpected discovery exception.
9. Repeated Refresh.
10. Device selection updates Channel ComboBox.
11. Hardware removed between Refresh operations.
12. Preserving selection when device remains available.
13. Connect disabled without a valid device/channel.
14. Refresh does not open a CAN bus.
15. Refresh does not disconnect an active session.
16. Existing CANService tests remain compatible.
17. Existing CAN Interface GUI tests remain compatible after adapting tests that assumed hardcoded devices.

Tests must run without real Vector hardware.

Do not falsely report hardware integration tests as passed.

## 13. Scope Restrictions

Do not implement:

- CAN Frame transmission
- CAN Frame reception
- CAN monitoring
- CAN logging
- CAN FD transmission
- ISO-TP
- UDS
- ECU scanning
- Diagnostic Sequence execution
- Security Access
- Seed-Key
- Flashing
- Database changes
- Unrelated GUI redesign

Do not modify diagnostic sequence widgets unless required for an immediate compatibility fix.

Do not delete existing features.

## 14. Acceptance Criteria

Milestone 01 is complete when:

- The application starts without Vector hardware.
- Refresh does not crash.
- A real supported Vector device can be discovered when the driver and hardware are available.
- Device and Channel ComboBoxes are populated from discovery results.
- Channels belong to the selected physical device.
- Multiple devices are distinguishable.
- The GUI does not invent missing devices.
- Existing connection behavior is preserved.
- Error messages distinguish driver problems from absent hardware.
- Automated tests pass.
- No CAN traffic is transmitted during discovery.

Hardware acceptance requires a separate manual test with VN1630A or VN1640A.

## 15. Final Deliverables

After implementing Milestone 01, report:

1. Changed files.
2. New public data models.
3. Discovery API and actual installed python-can version used.
4. Device/channel mapping logic.
5. Error handling.
6. Threading decisions.
7. Automated test results.
8. Hardware tests not yet performed.
9. Known limitations.
10. Changes required for Milestone 02.

Suggested commit message:

`CAN Interface - M01 Vector Device Discovery`

Do not proceed to Milestone 02 automatically.

Implement Milestone 01 completely, not as pseudocode.