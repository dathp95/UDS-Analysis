"""Data-only external .diag adapter. Never imports Qt, DLLs or execution rules."""
import json
from pathlib import Path

from core.diagnostic_sequence import DiagnosticStep, DiagnosticTestCase
from repositories.diagnostic_sequence_repository import DiagnosticSequenceRepository, DiagnosticSequenceValidationError as Invalid


def _text(value, field, *, optional=False):
    if value is None and optional:
        return ""
    if not isinstance(value, str) or (not optional and not value.strip()):
        raise Invalid(f"{field} must be {'nullable text' if optional else 'nonempty text'}.")
    return value.strip()


def _integer(value, field, minimum):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise Invalid(f"{field} must be an integer >= {minimum}.")
    return value


def import_diag(path):
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, ValueError) as error:
        raise Invalid(f"Cannot import {source.name}: invalid or unreadable JSON.") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("Header"), dict) or not isinstance(payload.get("TestCaseItem"), list):
        raise Invalid(f"{source.name}: Header must be an object and TestCaseItem must be a list.")
    steps = []
    for index, item in enumerate(payload["TestCaseItem"], 1):
        if not isinstance(item, dict) or not isinstance(item.get("ECUObj"), dict):
            raise Invalid(f"Step {index}: expected an object with ECUObj.")
        ecu = _text(item["ECUObj"].get("ECUName"), f"step {index} ECUName")
        request = _text(item.get("TransMess"), f"step {index} TransMess")
        expected = _text(item.get("ExpectMess"), f"step {index} ExpectMess", optional=True)
        # Reuse the native repository's byte-token HEX policy; no divergent parser.
        request = DiagnosticSequenceRepository._normalize_hex(request, f"step {index} TransMess")
        expected = DiagnosticSequenceRepository._normalize_hex(expected, f"step {index} ExpectMess", allow_empty=True)
        steps.append(DiagnosticStep(index, source.stem, ecu, request,
                     _integer(item.get("DelayTime", 100), f"step {index} DelayTime", 0),
                     _integer(item.get("RepeatTimes", 1), f"step {index} RepeatTimes", 1), expected, "prefix",
                     _text(item.get("Remark"), f"step {index} Remark", optional=True)))
    return DiagnosticTestCase(1, source.stem, _text(payload["Header"].get("Description"), "Description", optional=True), True, steps)
