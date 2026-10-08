# License Activation Core V1

## Migration behavior

- `activation.dat` is the intended persistent activation record for V-CODE activation.
- Existing `license/license.lic` files are legacy artifacts and no longer grant Full Mode.
- Startup validates the saved activation token signature, Device ID, and expiration every time.
- Missing, corrupt, expired, forged, or copied activation records leave the app in Limited Mode.

## Security notes

- Device IDs are SHA-256-derived fingerprints. They do not expose raw MachineGuid values.
- MachineGuid-based binding is useful for offline licensing, but it is not tamper-proof hardware attestation.
- The trusted public key is embedded in application code; replaceable external `public.pem` files are not trusted.
- Production private keys must be generated and stored offline outside this repository.
- Offline expiration depends on the local system clock. A fully offline app cannot prove trusted time without an external time source or secure hardware.
