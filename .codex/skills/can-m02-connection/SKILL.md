# V-CODE — CAN Interface Milestone 02

## Vector Connection Management

### Role

Act as a senior automotive software engineer specializing in Python, PySide6, python-can, Vector XL Driver and hardware lifecycle management.

Repository: `dathp95/UDS-Analysis`

Previous milestone: M01 Vector Device Discovery, implemented in commit `604dfe4020f10e3c8786e76ecc6463e2bb3f482b`.

Implement Milestone 02 only.

**Primary objective:** Establish safe and reliable Vector CAN connection management without implementing CAN TX/RX or UDS communication.

## 1. Review Existing Implementation

Read these files before editing:

- `gui/tabs/can_interface_tab.py`
- `services/can/can_service.py`
- `services/can/vector_backend.py`
- `services/can/can_config.py`
- `services/can/can_device.py`
- `gui/workers/can_discovery_worker.py`
- `services/can/__init__.py`
- `tests/services/test_can_service.py`
- `tests/services/test_vector_discovery.py`
- `tests/gui/test_can_interface_tab.py`
- `tests/gui/test_can_discovery_worker.py`
- `docs/can_interface/M01_DEVICE_DISCOVERY_REPORT.md`

Also inspect installed python-can version, existing test conventions and application shutdown lifecycle.

Use `XL_Driver_Library_Manual_EN.pdf` as reference when accessible.

Preserve M01 behavior and current GUI layout.

## 2. Scope

Implement:

1. Reliable Connect.
2. Reliable Disconnect.
3. Safe Reconnect after disconnection.
4. Correct hardware/channel selection.
5. Connection state management.
6. Background connection operations.
7. Robust error handling.
8. Cleanup and recovery.
9. Unit tests with mocked hardware.
10. Hardware acceptance checklist.

Do not implement CAN frame transmission, reception, ISO-TP, UDS or Diagnostic Sequence execution.

## 3. State Machine

Define a centralized typed connection state.

Required states:

- DISCONNECTED
- CONNECTING
- CONNECTED
- DISCONNECTING
- ERROR

Optional:

- HARDWARE_LOST
- RECOVERY_REQUIRED

Avoid relying on a GUI label as the source of truth.

State transitions must be explicit and validated.

Examples:

DISCONNECTED → CONNECTING → CONNECTED

DISCONNECTED → CONNECTING → ERROR → DISCONNECTED after successful cleanup

CONNECTED → DISCONNECTING → DISCONNECTED

CONNECTED → hardware error → recovery/cleanup → DISCONNECTED or RECOVERY_REQUIRED

Do not report DISCONNECTED if ownership of the native CAN resource is still uncertain.

## 4. Correct Device / Channel Selection

M01 introduced:

- CANDeviceInfo
- CANChannelInfo
- CANConfig.serial
- CANConfig.channel_index

Preserve these models.

When connecting, verify the selected device and channel.

Use the detected global channel index and required identity metadata to open the intended Vector CAN channel.

Do not infer a channel from the UI label.

Do not assume CAN 1 always maps to global index 0.

Do not assume the serial number alone uniquely identifies a channel.

Check how the installed python-can VectorBus handles `channel`, `serial`, `channel_index`, `app_name` and bitrate.

Use only supported python-can arguments.

When device/channel identity is ambiguous, refuse connection with a meaningful error.

Do not silently fall back to a different channel.

If revalidation before opening is necessary, implement it in the backend without changing the selected target or disrupting active sessions.

Do not call Refresh automatically from Connect unless the operation is explicitly designed and tested.

## 5. Connection Configuration

Preserve backward compatibility with:

```python
CANConfig(
    interface="vector",
    channel=0,
    bitrate=500000,
)
```

The UI should construct a configuration from the selected discovered channel.

Example:

```python
CANConfig(
    interface="vector",
    channel=selected_channel.channel,
    bitrate=selected_bitrate,
    serial=selected_device.serial,
    channel_index=selected_channel.channel_index,
)
```

Treat this as a required mapping pattern, not proof that a specific driver will accept every combination.

Validate:

- Interface is Vector.
- Selected hardware identity is valid.
- Channel index is valid.
- Bitrate is supported.
- Configuration has not changed while an operation is running.

Freeze the selected configuration at Connect start.

## 6. VectorBackend Connection Lifecycle

Update:

`services/can/vector_backend.py`

### Connect

Requirements:

- Reject a second connection when already connected.
- Do not silently close an active bus to open another.
- Create a new bus only when disconnected.
- Handle python-can and XL Driver exceptions.
- Preserve the original exception cause for logging.
- Do not report success until bus initialization completes.
- Never leave a partially initialized bus published as connected.
- Clean up partially allocated resources when possible.
- Do not silently retry with a different hardware channel.

### Disconnect

Requirements:

- Call `bus.shutdown()` when appropriate.
- Make repeated Disconnect requests safe.
- Release resources exactly once when possible.
- Avoid losing the bus reference before cleanup outcome is known.
- Handle exceptions during shutdown.
- Record cleanup failure distinctly from clean disconnection.
- Never allow simultaneous Connect and Disconnect operations.

Be careful with partial cleanup: a native driver error may leave resource ownership uncertain. Do not blindly attempt an unlimited number of retries.

### Reconnect

Allow reconnect only when the previous connection has been safely closed.

If the previous cleanup failed, expose a recovery state and refuse a new connection until resource ownership is resolved.

Do not implement automatic infinite retries.

## 7. CANService Responsibilities

Update:

`services/can/can_service.py`

CANService must own the connection lifecycle and expose a consistent public state.

Responsibilities:

- Validate configuration.
- Serialize connection operations.
- Delegate hardware operations to VectorBackend.
- Store active connection configuration.
- Distinguish successful opening from GUI status.
- Reject invalid state transitions.
- Report errors clearly.
- Expose connected device/channel details.
- Prevent Refresh during active connection operations.

Use thread-safe synchronization where operations can run on different threads.

Do not introduce unnecessary global state.

Keep discovery and connection functionality compatible.

## 8. QThread / Worker

Create or adapt a connection worker, for example:

`gui/workers/can_connection_worker.py`

Use a QObject worker with QThread, consistent with project conventions.

Operations:

- CONNECT
- DISCONNECT

Signals should communicate:

- Operation started
- Connection succeeded
- Disconnection succeeded
- Operation failed
- Operation finished

Requirements:

- Do not modify Qt widgets from worker threads.
- Prevent duplicate operations.
- Prevent Connect and Disconnect from overlapping.
- Ensure status updates occur on GUI thread.
- Handle application/tab shutdown safely.
- Never use QThread.terminate().
- Never destroy a running QThread.
- Do not block the GUI thread using unbounded wait().
- Do not report operation success before the worker has completed the hardware operation.
- Ensure one terminal outcome per operation.
- Avoid stale worker results overwriting newer states.

Review M01 QThread lifecycle for compatibility.

### Important threading design

Native Vector operations and bus ownership must be coordinated.

Do not assume that `can.Bus()` and `bus.shutdown()` are safe to execute concurrently from unrelated threads.

Prefer serialized backend operations under a controlled executor or worker lifecycle.

Do not create a separate thread for every operation without proving resource ownership and cleanup safety.

The worker architecture must remain extensible for M03 CAN TX/RX.

## 9. GUI Behavior

Update:

`gui/tabs/can_interface_tab.py`

Keep the existing top configuration/action row.

Do not redesign the Diagnostic Sequence widgets.

### DISCONNECTED

- Refresh enabled.
- Device and Channel enabled when populated.
- Bitrate enabled.
- Connect enabled only with valid selection.
- Disconnect disabled.

### CONNECTING

- Refresh disabled.
- Configuration ComboBoxes disabled.
- Connect disabled.
- Disconnect disabled.
- Status shows Connecting.

### CONNECTED

- Refresh disabled.
- Configuration ComboBoxes disabled.
- Connect disabled.
- Disconnect enabled.
- Status shows Connected.

Display selected hardware/channel information in tooltip or a suitable existing UI element.

### DISCONNECTING

- All connection operation buttons disabled.
- Configuration ComboBoxes disabled.
- Status shows Disconnecting.

### ERROR

- Show concise error details.
- Restore only controls that are safe for the confirmed resource state.
- Do not enable Connect if resource ownership is uncertain.

Preserve Light/Dark theme handling.

## 10. Error Handling

Distinguish errors such as:

- python-can missing.
- Vector XL Driver missing.
- No hardware.
- Selected hardware disconnected.
- Channel unavailable.
- Channel busy.
- Invalid bitrate.
- Driver initialization failure.
- Disconnect failure.
- Hardware lost during active session.
- Unexpected backend exception.

Use typed exceptions where beneficial.

Do not match only generic text when more precise exception types or error codes are available.

Maintain logging for technical diagnostics without exposing unnecessary driver internals to users.

## 11. Device Unplug Behavior

Handle USB disconnection gracefully when an interaction with the driver reports hardware loss.

Do not claim continuous hardware monitoring unless an actual mechanism is implemented.

If device loss is detected:

- Update state.
- Prevent further use of invalid connection.
- Attempt safe resource cleanup where appropriate.
- Preserve meaningful error information.
- Require rediscovery before selecting a newly connected device when needed.

Do not create a polling loop solely to simulate hardware monitoring.

## 12. Tests

Add or extend automated tests for:

1. Successful Connect.
2. Successful Disconnect.
3. Connect without discovered device.
4. Connect with invalid channel mapping.
5. Multiple devices and correct channel selection.
6. Duplicate Connect.
7. Duplicate Disconnect.
8. Connect while Disconnect is running.
9. Disconnect while Connect is running.
10. Connect exception.
11. Driver missing.
12. Device unplug before Connect.
13. Device unavailable during Connect.
14. Disconnect exception.
15. Partial initialization failure.
16. Cleanup failure and recovery state.
17. Reconnect after successful Disconnect.
18. Refresh blocked during Connect/Disconnect.
19. GUI remains responsive during slow Connect.
20. GUI remains responsive during slow Disconnect.
21. Application closes during an active operation.
22. Late worker results.
23. Worker lifecycle and cleanup.
24. Previous M01 regression tests.
25. Previous Diagnostic Sequence GUI tests.

Mock Vector hardware and python-can for automated tests.

Do not require VN1630A or VN1640A for CI.

Do not claim real hardware validation from mocked tests.

## 13. Hardware Acceptance

Provide a manual test checklist for Windows with Vector hardware.

Suggested hardware:

- VN1630A
- VN1640A

Test:

- Driver installed.
- Device detected.
- Correct serial displayed.
- Correct channel displayed.
- Connect using selected CAN channel.
- Disconnect.
- Reconnect.
- Switch channel after Disconnect.
- Unplug device before Connect.
- Unplug device while Connected.
- Attempt to connect a channel already used by another application.
- Restart V-CODE and repeat.

Use a properly configured bench/test network.

Do not transmit arbitrary frames to a production vehicle as part of M02 testing.

## 14. Restrictions

Do not implement:

- CAN TX/RX APIs for general application use.
- Frame monitoring.
- CAN logging.
- CAN FD communication.
- ISO-TP.
- UDS.
- Security Access.
- ECU flashing.
- Diagnostic Sequence runner.
- Database storage.
- Unrelated GUI changes.
- Licensing modifications.

Do not rewrite Device Discovery unless necessary to fix a regression.

Do not introduce direct custom XL Driver ctypes implementations without a documented need.

## 15. Documentation

Create:

`docs/can_interface/M02_CONNECTION_MANAGEMENT_REPORT.md`

Include:

- Architecture
- Changed files
- State machine
- Device/channel mapping
- Thread ownership
- Error handling
- Resource cleanup
- Test results
- Hardware validation still required
- Known limitations
- Readiness for M03

## 16. Acceptance Criteria

Milestone 02 is complete when:

- The correct selected channel is passed to Vector.
- Connect is asynchronous from the GUI perspective.
- The UI remains responsive.
- Connection state transitions are valid.
- Disconnect releases resources safely.
- Duplicate operations are prevented.
- Reconnect works after successful cleanup.
- Errors are shown without crashing the application.
- Partial initialization failures do not falsely report Connected.
- Uncertain resource ownership is not reported as a clean Disconnect.
- M01 discovery remains functional.
- Automated tests pass.

Hardware verification remains separately required before release.

Suggested commit:

`CAN Interface - M02 Vector Connection Management`

Do not implement Milestone 03 automatically.

Implement the complete M02 feature with production-oriented error handling and tests.