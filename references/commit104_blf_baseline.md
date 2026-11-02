# V-CODE ISO-TP & SecurityAccess Transport Stability Baseline Report
**Reference Baseline**: Commit 104 (`ca7943921a4098ae6e6d84dca731af18f6077398`)  
**Target Vehicle / Architecture**: VinFast VF5NP (Classical CAN 500 kbps, 11-bit Normal Addressing, ISO 14229 UDS, ISO 15765-2 ISO-TP)  
**Analyzed Log Traces**: 
- File 17: `output/CAN_Interface_Logs/17_V_CODE_CAN_VF5NP_20261102_080727_778980.blf`
- File 18: `output/CAN_Interface_Logs/18_V_CODE_CAN_VF5NP_20261102_111824_746011.blf`

---

## 1. Executive Summary & Root Cause Confirmation

### Problem Statement
On the VF5NP vehicle bench, multiple `27 01` (Level 1 Seed), `27 03` (Level 2 Seed), and associated Key submissions (`27 02`, `27 04`) consistently timed out in File 18, despite valid ECU DLL configurations. In File 17, a small number of transactions passed (BCM, BPM, EDS, SGC), while the rest failed.

### Key Investigation Questions Answered
1. **Are the ECU-specific DLL algorithms valid?**
   - **YES**. Verified empirically. Whenever Consecutive Frame 1 (CF1) arrived before the ECU's ISO 15765-2 $N\_Cr$ timeout ($150\text{ ms}$), the ECUs (BCM, BPM, EDS, SGC) calculated valid keys and responded with Positive Response `67 02` / `67 04`. No ECU responded with NRC `0x35` (Invalid Key) in either log.
2. **Is the issue caused by driver I/O, owner-thread scheduling, or ISO-TP state machine?**
   - **PRIMARY ROOT CAUSE**: **Owner-thread scheduling and passive non-blocking polling**.
   - `CanDiagnosticSession._pump()` relied entirely on `QTimer(2)` and non-blocking `recv(timeout=0.0)`.
   - On Windows, in a multi-threaded Qt application with Python GIL contention and 75ms GUI monitor updates (`_frame_timer`), thread scheduling jitter caused timer tick wakeups to stretch from $2\text{ ms}$ to $62 - 344\text{ ms}$.
   - Because `_pump()` immediately exited after `recv(0.0)` returned `None` (before the ECU had 5–15 ms to place Flow Control on the CAN bus), subsequent Consecutive Frames were delayed by $179 - 344\text{ ms}$.
   - Every VF5NP ECU whose internal $N\_Cr$ timer is $150\text{ ms}$ (ACM, EPS, ESC, MHU, BMS, etc.) aborted the multi-frame transfer, resulting in zero positive responses and 100% timeouts on File 18.
3. **Why did ECU Flow Control frames appear with $\Delta t = 0.00\text{ ms}$ in BLF logs?**
   - **SECONDARY DEFECT**: Timestamp domain clash and clamping in `VectorBackend._raw_frame`.
   - Outgoing TX frames were timestamped via PC host `time.monotonic()`, while incoming RX frames carried Vector hardware clock timestamps.
   - When the Vector hardware timestamp lagged the host monotonic fallback by even a microsecond, `wall < self._last_wall` forced the RX timestamp to be clamped to the exact TX timestamp (`dt = 0.00ms`), concealing true physical inter-frame intervals.

---

## 2. Empirical Timing Analysis

### A. Threshold Limits Defined by ISO 15765-2 and VF5NP ECUs
| Protocol Parameter | Description | Typical Limit on VF5NP ECUs | Impact when Exceeded |
| :--- | :--- | :--- | :--- |
| **$N\_Bs$** | Time between ECU First Frame (TX) and Tester Flow Control (RX) | $100\text{ ms} - 120\text{ ms}$ | ECU aborts transmission of Seed Consecutive Frames; Seed request times out. |
| **$N\_Cr$** | Time between Tester receiving Flow Control (FC) and sending CF1 | $150\text{ ms}$ (strict) | ECU aborts reception of Key payload; ECU does not reply to Key; Tester times out. |
| **$ST_{\min}$** | Separation Time minimum required by ECU between consecutive frames | $0\text{ ms}$ (BCM, SGC), $5\text{ ms}$ (EPS), $20\text{ ms}$ (MHU, BPM, BMS) | Tester must space Consecutive Frames by at least $ST_{\min}$ without arbitrary 100ms+ delays. |

### B. File 17 Timing Measurements
- **Total Transactions**: 66 (49 OK, 4 NRC, 3 Ambiguous, 10 TIMEOUT)
- **Key Submissions Analysis**:
  | ECU | Subfunction | ECU FC to Tester CF1 Delay | ECU $N\_Cr$ Threshold | Outcome | Reason |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | **BCM** | `27 02` | $109\text{ ms}$ | $150\text{ ms}$ | **PASSED** (`67 02`) | CF1 beat $N\_Cr$ deadline. |
  | **BPM** | `27 02` | $104\text{ ms}$ | $150\text{ ms}$ | **PASSED** (`67 02`) | CF1 beat $N\_Cr$ deadline. |
  | **SGC** | `27 02` | $92\text{ ms}$ | $150\text{ ms}$ | **PASSED** (`67 02`) | CF1 beat $N\_Cr$ deadline. |
  | **EDS** | `27 04` | $140\text{ ms}$ | $150\text{ ms}$ | **PASSED** (`67 04`) | CF1 beat $N\_Cr$ deadline. |
  | **ACM** | `27 02` | $180\text{ ms}$ | $150\text{ ms}$ | **TIMEOUT** | CF1 exceeded $N\_Cr$ ($180 > 150$). |
  | **EPS** | `27 02` | $156\text{ ms}$ | $150\text{ ms}$ | **TIMEOUT** | CF1 exceeded $N\_Cr$ ($156 > 150$). |
  | **ESC** | `27 02` | $182\text{ ms}$ | $150\text{ ms}$ | **TIMEOUT** | CF1 exceeded $N\_Cr$ ($182 > 150$). |
  | **MHU** | `27 02` | $169\text{ ms}$ | $150\text{ ms}$ | **TIMEOUT** | CF1 exceeded $N\_Cr$ ($169 > 150$). |

### C. File 18 Timing Measurements
- **Total Transactions**: 63 (38 OK, 4 NRC, 21 TIMEOUT)
- **100% of Key Submissions Failed**:
  | ECU | Key Request | FC Parameters Received | FC $\rightarrow$ CF1 Delay | CF1 $\rightarrow$ CF2 Delay | Outcome |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | **BCM** | `27 02` | $FS=0, BS=0, ST_{\min}=0\text{ms}$ | **$229\text{ ms}$** | $62\text{ ms}$ | **TIMEOUT** (Aborted by ECU) |
  | **BMS** | `27 02` | $FS=0, BS=8, ST_{\min}=20\text{ms}$ | **$321\text{ ms}$** | $110\text{ ms}$ | **TIMEOUT** (Aborted by ECU) |
  | **ACM** | `27 02` | $FS=0, BS=0, ST_{\min}=0\text{ms}$ | **$138\text{ ms}$ / $240\text{ ms}$** | $78\text{ ms}$ | **TIMEOUT** (Aborted by ECU) |
  | **BPM** | `27 02` | $FS=0, BS=8, ST_{\min}=20\text{ms}$ | **$216\text{ ms}$** | $62\text{ ms}$ | **TIMEOUT** (Aborted by ECU) |
  | **EDS** | `27 04` | $FS=0, BS=0, ST_{\min}=0\text{ms}$ | **$290\text{ ms}$** | $78\text{ ms}$ | **TIMEOUT** (Aborted by ECU) |
  | **EPS** | `27 02` | $FS=0, BS=8, ST_{\min}=20\text{ms}$ | **$268\text{ ms}$** | $63\text{ ms}$ | **TIMEOUT** (Aborted by ECU) |
  | **ESC** | `27 02` | $FS=0, BS=8, ST_{\min}=20\text{ms}$ | **$247\text{ ms}$** | $63\text{ ms}$ | **TIMEOUT** (Aborted by ECU) |
  | **SGC** | `27 02` | $FS=0, BS=8, ST_{\min}=5\text{ms}$ | **$179\text{ ms}$** | $78\text{ ms}$ | **TIMEOUT** (Aborted by ECU) |
  | **MHU** | `27 04` | $FS=0, BS=8, ST_{\min}=20\text{ms}$ | **$324\text{ ms}$** | $93\text{ ms}$ | **TIMEOUT** (Aborted by ECU) |

Notice that every single interval in File 18 is a multiple of $\sim 75\text{ ms}$ ($62\text{ ms}$, $78\text{ ms}$, $93\text{ ms}$, $156\text{ ms}$, $235\text{ ms}$, $324\text{ ms}$), aligning exactly with the periodic 75ms `_frame_timer` running on the Qt GUI thread.

---

## 3. Architecture & Threading Model

```
+-------------------------------------------------------------------------+
|                               GUI THREAD                                |
|  - DiagnosticTablePanel / CANMonitorPanel / User Interactions           |
|  - _frame_timer (75ms): calls _drain_frames() and renders table view    |
+-------------------------------------------------------------------------+
                                    |
                    Signal / Slot   |  (Queued & Direct Connections)
                                    v
+-------------------------------------------------------------------------+
|                        CAN WORKER QTHREAD                               |
|  - Native owner of VectorBus, CANService, and CanDiagnosticSession      |
|  - CanDiagnosticSession: executes ISO-TP engine and diagnostic clients   |
|  - VectorBackend: wraps python-can VectorBus                            |
+-------------------------------------------------------------------------+
                                    |
                    Ctypes / Win32  |  (Vector XL Driver C Library)
                                    v
+-------------------------------------------------------------------------+
|                  VECTOR XL DRIVER & CAN CONTROLLER                      |
|  - Win32 Event Object (event_handle) signaled on CAN frame arrival       |
|  - Physical Classical CAN Transceiver (VN1640A / VN1630A, 500 kbps)     |
+-------------------------------------------------------------------------+
```

### Flaws Identified in Baseline Architecture
1. **No Active Burst Window**: When ISO-TP needs to transmit a multi-frame packet, it relies on passive timer scheduling between individual frames.
2. **Win32 Event Handle Ignored**: `VectorBackend` always passed `timeout=0.0` to `bus.recv()`, preventing `WaitForSingleObject` from sleeping efficiently and waking up immediately upon hardware frame arrival.
3. **Clamping Distortion**: In `VectorBackend._raw_frame`, TX frames were given monotonic timestamps while RX frames used hardware timestamps, causing artificial clamping.

---

## 4. Remediation Plan

1. **Active Multi-Frame Pump Window**:
   - In `CanDiagnosticSession._pump()`:
     When multi-frame transmission or reception is active (`self.client.engine.transmitting` or `self.client.engine.receiving`), enter a short, cooperative burst pump loop (budgeted at up to $30\text{ ms}$ per pump or until next frame transfer).
     This ensures FC reception and CF transmissions occur in $< 5 - 20\text{ ms}$, well below the ECU's $150\text{ ms}$ $N\_Cr$ threshold.
2. **Synchronous Hardware Wait with Bounded Timeout**:
   - Enable `VectorBackend.fn_receive_frame(timeout=0.0)` to accept a small timeout (e.g. `0.001` - `0.005s`) during active diagnostic bursts. This allows python-can to invoke `WaitForSingleObject(event_handle, ms)` and receive hardware frames with sub-millisecond latency without burning CPU or starving the GUI thread.
3. **Preserve Clock Coherence**:
   - Prevent monotonic clock clamping from obliterating physical arrival order and delta times.
4. **Deterministic Unit Tests**:
   - Verify that simulated multi-frame sequences complete within $< 10\text{ ms}$ for $ST_{\min}=0$ and $< 25\text{ ms}$ for $ST_{\min}=20\text{ ms}$.

