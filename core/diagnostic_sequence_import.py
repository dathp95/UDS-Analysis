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
        ecu_obj = item["ECUObj"]

        source_request_id = _can_id(
            ecu_obj.get("IDReq"),
            f"step {index} IDReq",
        )

        source_response_id = _can_id(
            ecu_obj.get("IDResp"),
            f"step {index} IDResp",
        )
        
        # Preserve incomplete payloads during import.
        # HEX validation belongs to the UDS send operation.

        request = item.get("TransMess", "")
        expected = item.get("ExpectMess", "")

        if request is None:
            request = ""

        if expected is None:
            expected = ""

        if not isinstance(request, str):
            raise Invalid(
                f"Step {index}: TransMess must be text."
            )

        if not isinstance(expected, str):
            raise Invalid(
                f"Step {index}: ExpectMess must be text."
            )

        # Preserve the original input.
        # Do not reject empty or incomplete HEX.
        
        expected = DiagnosticSequenceRepository._normalize_hex(expected, f"step {index} ExpectMess", allow_empty=True)
        # Read step name from the original .diag file.
        sequence_name = _text(
            item.get("SeqName"),
            f"step {index} SeqName",
            optional=True,
        )
        steps.append(
            DiagnosticStep(
                step=index,
                sequence_name=sequence_name,
                source_request_id=source_request_id,
                source_response_id=source_response_id,
                ecu=ecu,
                request=request,
                delay_ms=_integer(
                    item.get("DelayTime", 100),
                    f"step {index} DelayTime",
                    0,
                ),
                repeat=_integer(
                    item.get("RepeatTimes", 1),
                    f"step {index} RepeatTimes",
                    1,
                ),
                expected_response=expected,
                match="prefix",
                comment=_text(
                    item.get("Remark"),
                    f"step {index} Remark",
                    optional=True,
                ),
            )
        )
    return DiagnosticTestCase(1, source.stem, _text(payload["Header"].get("Description"), "Description", optional=True), True, steps)

def _can_id(value, field):
    # Some older DIAG files may not include CAN addressing.
    if value is None:
        return None

    if isinstance(value, bool) or not isinstance(value, int):
        raise Invalid(
            f"{field} must be a decimal integer."
        )

    if not 0 <= value <= 0x7FF:
        raise Invalid(
            f"{field} must be an 11-bit CAN ID."
        )

    return value
