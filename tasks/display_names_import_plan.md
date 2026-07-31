# Plan: Import display names from Vehicle Manager

1. Add validated atomic import helpers for JSON and pipe-delimited rules.
2. Normalize rule payload whitespace/hex casing and merge/update the mapping.
3. Add runtime reload support to `core.uds_lookup`.
4. Add `Import Display Names` and `Import Display Rules` actions to `VehicleManagerTab`.
5. Add core and GUI regression tests.
6. Run focused tests, full suite, syntax check and diff review.
