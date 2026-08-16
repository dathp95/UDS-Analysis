# Coding Value MethodType Hyphen Format

## Request
Support `$MethodType` values using a hyphen separator, for example:

```text
0x01 - ABC
0X01 - ABC
```

## Changes
- Updated the Coding Value option parser to accept `=`, `:`, and `-` separators.
- Updated the parser to accept both `0x` and `0X` hex prefixes.
- Added a core regression test for hyphen-separated `$MethodType` values.

## Verification
- `python -m unittest tests.core.test_coding_value_excel`
- `python -m py_compile core\coding_value.py tests\core\test_coding_value_excel.py`
