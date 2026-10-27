---
name: vcode-security-seed-request
description: Implement and verify V-CODE CAN Interface Commit 78 Milestone 1: request UDS SecurityAccess seed with 27 01 and display 67 01 seed, without any key sending or DLL integration.
---

# V-CODE Commit 78 — SecurityAccess Request Seed (Milestone 1)

## Purpose
Enable **only** UDS `27 01` (SecurityAccess requestSeed subfunction 0x01) on authorized test bench/ECU configurations. Display the exact UDS response including seed, correlate transactions safely, and retain existing CAN/ISO-TP monitoring. This milestone MUST NOT calculate keys, invoke OEM DLLs, perform `27 02`, unlock an ECU, or broaden access to other `0x27` subfunctions.

## Repository and baseline
- Repo: `dathp95/UDS-Analysis`.
- Baseline: Commit 77 `19c2024cc888893323ac2757816a01add0f19da7`. Check current working tree and actual source before editing. Do not overwrite newer changes or user edits.
- Python 3.12 / PySide6. Follow existing repository patterns and tests.

## Primary files to inspect
- `core/diagnostic_request.py`: `DiagnosticRequest.__post_init__`, service admission, `response_belongs_to_request`, send policy.
- `gui/widgets/can_interface/diagnostic_table_panel.py`: `_request_step`, `_set_button_state`, payload validity.
- `gui/controllers/can_diagnostic_controller.py`: `send_row`, `_result`, cancellation, connection state.
- `services/can/ecu_diagnostic_resolver.py`: request builder and vehicle/ECU CAN ID resolution.
- Existing diagnostic transport and mock/test suites: find the actual files before writing tests.
- `services/seed_key_provider.py` is mock-only and OUT OF SCOPE.

## Required behavior
1. Admit exactly two bytes `27 01` as a manual request; no extra payload bytes. Do not treat `27 01 xx`, `27 02`, `27 03`, or any other `0x27` request as allowed. Keep existing physical 11-bit addressing, ECU validation, connection checks, request length bounds, authorization policy for other services, and diagnostic cancellation.
2. GUI enables row Send `>` for exactly `27 01` only when HEX is valid, a unique configured ECU is selected, and connection is ready. Invalid HEX and other `0x27` subfunctions must remain disabled; backend validation must independently enforce allowlist.
3. Correlate a positive response only when SID is `67`, subfunction echo is `01`, and the response has at least one seed byte (`67 01 <seed...>`). Store/show complete response including seed in existing Receive Message UI. A response `67 01` without seed must not be considered successful. Do not assume one fixed seed length; obey existing ISO-TP payload size and response limits.
4. Support UDS negative responses `7F 27 <NRC>` using existing result handling, including cases such as NRC `7F`, `22`, `24`, `33`, `35`, `36`, `37`, `78`. `7F 27 78` remains response pending according to existing timing logic, not a positive seed. Wrong subfunction responses (e.g. `67 03 ...`) must not correlate to `27 01`.
5. Keep established result semantics: distinguish transaction correlation from test expectation and reported outcome. Inspect expected-response matching rules; if the table expects `67 01`, a positive response with a nonempty seed should be accepted by prefix matching, while a missing seed should never be reported Passed. Never log or persist raw seed in new telemetry or analytics; only display in the existing local diagnostic result/trace at operator request. Avoid writing sensitive seed into extra debug log statements.
6. Preserve current manual state-changing request confirmation behavior and authorized test-bench context. Do not suppress existing prompts broadly; add no background or automatic seed polling. Do not auto-send `10 03`: user controls diagnostic session and may get a negative response if wrong session.
7. Do not change `.diag`/`.json` editor/save, folder converter, Vehicle Manager, portable DLL architecture, BLF recording, or unrelated UI.

## Implementation guidance
- Introduce a narrow explicit allowlist constant for `b'\x27\x01'` (if no existing suitable policy helper). Update the `DiagnosticRequest` validation branch so `0x27` gets only that exception and other services still follow previous admission rules.
- Treat `0x27` positive echo length as one byte in `response_belongs_to_request`, verify echo equals `01`, and check nonempty seed. Follow existing code's suppress-positive-response mask behavior only where meaningful; do not accidentally accept `67 03` or zero-length seed.
- In the PySide6 table, parse the HEX tokens to bytes rather than relying on a raw string `startswith('27')`: this avoids false results for spacing/case or malformed tokens.
- Audit outcome evaluation and ISO-TP response processing to ensure no false PASS from empty `67 01` and no accidental timeout on valid multi-frame seed.
- Keep Send disabled for all unsupported 0x27 subfunctions at both GUI and core layers.

## Mandatory tests (use existing test conventions)
- `27 01` admitted through `DiagnosticRequest` and UI; `27 02`, `27 03`, `27 01 00` rejected by core; other preexisting allow/deny policies unchanged.
- Positive responses: `67 01 AB CD` matches; `67 01` rejected as successful positive; `67 03 AB CD`, `67 02 AB CD`, `67 01` wrong/corrupted framing not falsely Passed.
- `7F 27 33` correlates as negative; `7F 27 78` remains pending with existing timeout policy; unrelated `7F 22 31` does not belong to request.
- Correct behavior for lowercase/whitespace-normalized editor payload, invalid HEX, unresolved ECU, disconnected channel, cancellation and late response.
- Confirm manual diagnostic `10 03` and `22 F1 90`, existing bench policy, log monitor/BLF behavior are unchanged.
- Include mock transport tests; do not require a real ECU or Vector hardware for CI.

## Validation and deliverables
1. Run targeted new/existing diagnostic tests, syntax compile, and broader CAN regression tests if feasible. Capture exact commands and results; never claim a test passed if not run.
2. Summarize files changed, policy decisions, test evidence, and remaining limitations in `docs/can_interface/COMMIT78_SECURITY_REQUEST_SEED_REPORT.md`.
3. Do not perform a git commit or push unless explicitly requested. Do not change license/security-provider features.
4. Provide a brief manual bench checklist: establish selected Vector channel, choose Vehicle/ECU, explicitly enter required session (`10 03` if applicable), send `27 01`, inspect `67 01 + seed` or NRC, confirm no key submission.

## Definition of done
`27 01` is enabled as a single manual request on the CAN Interface, complete valid `67 01 + seed` is displayed and correctly correlated, unsupported `0x27` requests are blocked in core and UI, all existing safety guards remain, and regression tests are documented.
