from PySide6.QtCore import QObject, Signal, Slot

from core.asc_reader import get_log_channels


class LogChannelWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(
            self,
            log_file: str,
        ):
        super().__init__()
        self._log_file = log_file

    @Slot()
    def run(self):
        try:
            channels = get_log_channels(
                self._log_file
            )
        except Exception as exc:
            self.failed.emit(str(exc))
            return

        self.finished.emit(channels)
