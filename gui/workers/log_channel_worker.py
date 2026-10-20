from PySide6.QtCore import QObject, Signal, Slot
from pathlib import Path

from core.asc_reader import get_log_channels
from core.log_parsers.diagnostics import ParserDiagnostics


class LogChannelWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)
    diagnostics_ready = Signal(object)

    def __init__(
            self,
            log_file: str,
        ):
        super().__init__()
        self._log_file = log_file

    @Slot()
    def run(self):
        try:
            if Path(self._log_file).suffix.lower() == ".txt":
                diagnostics = ParserDiagnostics()
                channels = get_log_channels(self._log_file, diagnostics=diagnostics)
                self.diagnostics_ready.emit(diagnostics)
            else:
                channels = get_log_channels(self._log_file)
        except Exception as exc:
            self.failed.emit(str(exc))
            return

        self.finished.emit(channels)
