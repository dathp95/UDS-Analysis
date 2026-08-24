from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from config.paths import DIAGNOSTIC_SEQUENCES_DIR
from core.diagnostic_sequence import DiagnosticStep, DiagnosticTestCase


VALID_MATCH_TYPES = frozenset({
    "prefix",
    "exact",
    "wildcard",
})

_HEX_BYTE_PATTERN = re.compile(r"^[0-9A-Fa-f]{2}$")


class DiagnosticSequenceValidationError(ValueError):
    pass


class DiagnosticSequenceRepository:

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root is not None else DIAGNOSTIC_SEQUENCES_DIR

    def fn_list_sequences(self) -> list[Path]:
        if not self.root.exists():
            return []

        return sorted(
            path
            for path in self.root.iterdir()
            if path.is_file() and path.suffix.lower() == ".json"
        )

    def fn_load_sequence(self, path: str | Path) -> DiagnosticTestCase:
        sequence_path = Path(path)
        try:
            payload = json.loads(
                sequence_path.read_text(encoding="utf-8-sig")
            )
        except json.JSONDecodeError as error:
            raise DiagnosticSequenceValidationError(
                f"Invalid JSON in diagnostic sequence: {sequence_path}"
            ) from error
        except OSError as error:
            raise DiagnosticSequenceValidationError(
                f"Cannot read diagnostic sequence: {sequence_path}"
            ) from error

        return self._to_test_case(payload)

    def fn_save_sequence(
        self,
        test_case: DiagnosticTestCase,
        path: str | Path,
    ) -> Path:
        normalized = self._normalize_test_case(test_case)
        sequence_path = Path(path)
        sequence_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        sequence_path.write_text(
            json.dumps(
                self._test_case_to_json(normalized),
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return sequence_path

    def fn_update_sequence(
        self,
        test_case: DiagnosticTestCase,
        path: str | Path,
    ) -> Path:
        return self.fn_save_sequence(
            test_case,
            path,
        )

    def _to_test_case(self, payload: Any) -> DiagnosticTestCase:
        if not isinstance(payload, dict):
            raise DiagnosticSequenceValidationError(
                "Diagnostic sequence JSON must be an object."
            )

        self._require_key(payload, "schema_version")
        self._require_key(payload, "name")
        self._require_key(payload, "steps")

        steps_payload = payload["steps"]
        if not isinstance(steps_payload, list):
            raise DiagnosticSequenceValidationError(
                "Diagnostic sequence field 'steps' must be a list."
            )

        return DiagnosticTestCase(
            schema_version=self._to_int(
                payload["schema_version"],
                "schema_version",
            ),
            name=self._to_required_text(
                payload["name"],
                "name",
            ),
            description=self._to_text(
                payload.get("description", ""),
            ),
            enabled=self._to_bool(
                payload.get("enabled", True),
                "enabled",
            ),
            steps=[
                self._to_step(step_payload, index)
                for index, step_payload in enumerate(
                    steps_payload,
                    start=1,
                )
            ],
        )

    def _to_step(
        self,
        payload: Any,
        index: int,
    ) -> DiagnosticStep:
        if not isinstance(payload, dict):
            raise DiagnosticSequenceValidationError(
                f"Diagnostic sequence step {index} must be an object."
            )

        for field_name in (
            "step",
            "sequence_name",
            "ecu",
            "request",
        ):
            self._require_key(
                payload,
                field_name,
                context=f"step {index}",
            )

        delay_ms = self._to_int(
            payload.get("delay_ms", 100),
            f"step {index} delay_ms",
        )
        repeat = self._to_int(
            payload.get("repeat", 1),
            f"step {index} repeat",
        )
        match = self._to_text(
            payload.get("match", "prefix"),
        ).lower()

        if delay_ms < 0:
            raise DiagnosticSequenceValidationError(
                f"Diagnostic sequence step {index} delay_ms must be >= 0."
            )

        if repeat < 1:
            raise DiagnosticSequenceValidationError(
                f"Diagnostic sequence step {index} repeat must be >= 1."
            )

        if match not in VALID_MATCH_TYPES:
            raise DiagnosticSequenceValidationError(
                f"Diagnostic sequence step {index} match must be prefix, exact, or wildcard."
            )

        return DiagnosticStep(
            step=self._to_int(
                payload["step"],
                f"step {index} step",
            ),
            sequence_name=self._to_required_text(
                payload["sequence_name"],
                f"step {index} sequence_name",
            ),
            ecu=self._to_required_text(
                payload["ecu"],
                f"step {index} ecu",
            ),
            request=self._normalize_hex(
                payload["request"],
                f"step {index} request",
            ),
            delay_ms=delay_ms,
            repeat=repeat,
            expected_response=self._normalize_hex(
                payload.get("expected_response", ""),
                f"step {index} expected_response",
                allow_empty=True,
            ),
            match=match,
            comment=self._to_text(
                payload.get("comment", ""),
            ),
        )

    def _normalize_test_case(
        self,
        test_case: DiagnosticTestCase,
    ) -> DiagnosticTestCase:
        if not isinstance(test_case, DiagnosticTestCase):
            raise DiagnosticSequenceValidationError(
                "Expected DiagnosticTestCase."
            )

        return self._to_test_case(
            self._test_case_to_json(test_case)
        )

    @staticmethod
    def _test_case_to_json(
        test_case: DiagnosticTestCase,
    ) -> dict[str, Any]:
        return {
            "schema_version": test_case.schema_version,
            "name": test_case.name,
            "description": test_case.description,
            "enabled": test_case.enabled,
            "steps": [
                DiagnosticSequenceRepository._step_to_json(step)
                for step in test_case.steps
            ],
        }

    @staticmethod
    def _step_to_json(step: DiagnosticStep) -> dict[str, Any]:
        return {
            "step": step.step,
            "sequence_name": step.sequence_name,
            "ecu": step.ecu,
            "request": step.request,
            "delay_ms": step.delay_ms,
            "repeat": step.repeat,
            "expected_response": step.expected_response,
            "match": step.match,
            "comment": step.comment,
        }

    @staticmethod
    def _require_key(
        payload: dict[str, Any],
        field_name: str,
        context: str = "root",
    ) -> None:
        if field_name not in payload:
            raise DiagnosticSequenceValidationError(
                f"Diagnostic sequence missing required field '{field_name}' in {context}."
            )

    @staticmethod
    def _to_required_text(value: Any, field_name: str) -> str:
        text = DiagnosticSequenceRepository._to_text(value)
        if not text:
            raise DiagnosticSequenceValidationError(
                f"Diagnostic sequence field '{field_name}' must not be empty."
            )
        return text

    @staticmethod
    def _to_text(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _to_int(value: Any, field_name: str) -> int:
        if isinstance(value, bool):
            raise DiagnosticSequenceValidationError(
                f"Diagnostic sequence field '{field_name}' must be an integer."
            )

        try:
            return int(value)
        except (TypeError, ValueError) as error:
            raise DiagnosticSequenceValidationError(
                f"Diagnostic sequence field '{field_name}' must be an integer."
            ) from error

    @staticmethod
    def _to_bool(value: Any, field_name: str) -> bool:
        if not isinstance(value, bool):
            raise DiagnosticSequenceValidationError(
                f"Diagnostic sequence field '{field_name}' must be true or false."
            )
        return value

    @staticmethod
    def _normalize_hex(
        value: Any,
        field_name: str,
        allow_empty: bool = False,
    ) -> str:
        text = DiagnosticSequenceRepository._to_text(value)
        if not text:
            if allow_empty:
                return ""
            raise DiagnosticSequenceValidationError(
                f"Diagnostic sequence field '{field_name}' must contain HEX bytes."
            )

        tokens = text.split()
        if not tokens or any(
            not _HEX_BYTE_PATTERN.fullmatch(token)
            for token in tokens
        ):
            raise DiagnosticSequenceValidationError(
                f"Diagnostic sequence field '{field_name}' must contain valid HEX bytes."
            )

        return " ".join(
            token.upper()
            for token in tokens
        )
