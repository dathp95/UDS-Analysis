from pathlib import Path
from dataclasses import replace
import json
import os
import tempfile

from core.diagnostic_sequence_import import import_diag
from repositories.diagnostic_sequence_repository import DiagnosticSequenceRepository, DiagnosticSequenceValidationError
from core.diagnostic_sequence import DiagnosticStep

class CanSequenceRepository(DiagnosticSequenceRepository):
    """Read native JSON/external .diag; write native JSON only."""
    ALLOW_EMPTY_ECU = True  # Unresolved editor rows remain non-sendable drafts.
    def __init__(self, root=None, sources=()):
        super().__init__(root)
        self._external_sources = set()
        for source in sources:
            if source:
                try:
                    self.register_source(source)
                except (OSError, ValueError):
                    continue  # Malformed/stale preferences must not prevent startup.

    def register_source(self, source):
        path = Path(source).resolve()
        if path.suffix.lower() not in (".json", ".diag"):
            raise DiagnosticSequenceValidationError("Select a native .json or external .diag sequence.")
        self._external_sources.add(path)

    def fn_list_sequences(self):
        """
        List native V-CODE JSON sequences only.

        .diag files are accepted as import sources,
        not as editable library documents.
        """
        if not self.root.exists():
            return []

        return sorted(
            path.resolve()
            for path in self.root.iterdir()
            if path.is_file()
            and path.suffix.lower() == ".json"
        )

    def fn_load_sequence(self, path):
        suffix = Path(path).suffix.lower()
        if suffix == ".diag":
            return import_diag(path)
        if suffix != ".json":
            raise DiagnosticSequenceValidationError("Unsupported diagnostic sequence format.")
        try:
            return super().fn_load_sequence(path)
        except UnicodeError as error:
            raise DiagnosticSequenceValidationError(f"Cannot decode {Path(path).name} as UTF-8.") from error

    def fn_save_sequence(self, test_case, path):
        if Path(path).suffix.lower() != ".json":
            raise DiagnosticSequenceValidationError("Imported .diag is read-only. Save As V-CODE Sequence (.json).")
        normalized = self._normalize_test_case(test_case)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                             suffix='.tmp', delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(self._test_case_to_json(normalized), stream, indent=4, ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return path

    def _to_step(self, payload, index):
        if not isinstance(payload, dict):
            raise DiagnosticSequenceValidationError(
                f"Step {index} must be an object."
            )

        # Only relax HEX validation in CAN Sequence Editor.
        # Keep structural fields and numeric settings validated.
        draft = dict(payload)

        request = draft.get("request", "")
        expected = draft.get("expected_response", "")

        if not isinstance(request, str):
            raise DiagnosticSequenceValidationError(
                f"Step {index}: request must be text."
            )

        if not isinstance(expected, str):
            raise DiagnosticSequenceValidationError(
                f"Step {index}: expected_response must be text."
            )

        # Use valid placeholder bytes for the base validator.
        draft["request"] = "00"
        draft["expected_response"] = ""

        # The CAN editor supports incomplete sequence-name drafts.
        sequence_name = draft.get("sequence_name", "")

        if not isinstance(sequence_name, str):
            raise DiagnosticSequenceValidationError(
                f"Step {index}: sequence_name must be text."
            )

        # Use a temporary valid name for the strict base validator.
        draft["sequence_name"] = "_DRAFT_"

        step = super()._to_step(draft, index)

        return replace(
            step,
            sequence_name=sequence_name,
            request=request,
            expected_response=expected,
            comment=payload.get("comment", "")
            if isinstance(payload.get("comment", ""), str)
            else step.comment,
        )
