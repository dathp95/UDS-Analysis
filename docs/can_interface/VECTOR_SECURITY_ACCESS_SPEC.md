# Vector SecurityAccess integration

Source: Vector AN-IDG-1-017 v1.1 (2020-07-08), sections 1.1, 1.2.1/1.2.2:
https://cdn.vector.com/cms/content/know-how/_application-notes/AN-IDG-1-017_SecurityAccess.pdf

## Contract

Complete the existing L1 flow: manual `27 01`, correlated `67 01 + seed`,
deliberate Unlock L1, asynchronous verified key calculation, individual bench
confirmation, one-shot generated `27 02 + key`, exact correlated `67 02`.
Keep the existing CAN owner and ISO-TP path and manual-key prohibition.
Do not infer native calling convention or proprietary parameters from export names.

GenerateKeyEx consumes raw seed bytes/size, security level and variant, and returns
key bytes with actual length bounded by the caller's buffer capacity. The Opt
interface additionally requires the DLL-specific options string. Neither interface
defines a universal algorithm, seed/key length or OEM level/variant mapping.

Only a matching, offline-verified provider may authorize a physical key submission.
Current HMAC profile is 16-byte seed/key; simulator material stays memory-only and
cannot authorize a physical backend. No OEM DLL execution during this task until
its ABI and authorized reference vectors have been established.

Recognize zero seed as already unlocked; never calculate/send a key for it.
Cancellation, edits, selection/connection/session changes and expiry invalidate
the calculation and generated capability. Never retry a failed key automatically.
Report NRC 24/33/35/36/37 distinctly; keep NRC 78 pending until final/timeout.
Preserve editable sequence data and keep key results separate from seed results.

## Slices and verification

1. Run existing service/GUI Commit82 tests to establish missing-GUI baseline.
2. Add zero-seed/session and stale-result tests, then implement state semantics.
3. Connect an Unlock L1 action to an asynchronous worker and existing authority.
   Verify success, double click, declined confirmation, cancellation, missing
   provider, malformed response, pending and NRC paths with a simulated ECU.
4. Review policy boundaries, run CAN/sequence regressions and render Light/Dark UI.
5. Record actual test results and native-provider blockers separately.

Commands: `.venv\Scripts\python.exe -m unittest tests.services.test_security_access82 tests.gui.test_security_access82 -v`.
Patterns: frozen requests, QObject signals, unittest and temporary repositories.
No dependency, license, vehicle JSON, OEM binary or release feature changes.

## Native assets inspected

The supplied `Alll Key DLL VF5 NP` folder contains 16 x86 DLLs exporting
`GenerateKeyEx`; `BCM.dll.txt` is a hex dump, not a native header.
BCM SHA-256: `412b4e91bcf7aa7804cda0de6d83ea13a3425810c3507ba78f6dab031a2150da`.
Native ABI, return enumeration, level/variant mapping and verified vectors are
still required before enabling a real DLL provider.

`HandleDLL.cs` and `gen.txt` were also read in full. They prove the managed
seed->helper->key sequence, but CalulateKey's body is missing/invalid, the return
enum is absent and GenerateKeyEx has no calling-convention annotation. The Opt
delegate's Cdecl annotation does not establish GenerateKeyEx's ABI.
