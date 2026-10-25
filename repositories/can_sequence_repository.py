from pathlib import Path

from core.diagnostic_sequence_import import import_diag
from repositories.diagnostic_sequence_repository import DiagnosticSequenceRepository, DiagnosticSequenceValidationError


class CanSequenceRepository(DiagnosticSequenceRepository):
    """Read native JSON/external .diag; write native JSON only."""
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
        paths = set(self._external_sources)
        if self.root.exists():
            paths.update(path.resolve() for path in self.root.iterdir()
                         if path.is_file() and path.suffix.lower() in (".json", ".diag"))
        return sorted(paths)

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
        return super().fn_save_sequence(test_case, path)
