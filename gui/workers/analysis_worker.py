from PySide6.QtCore import QObject, Signal, Slot


class AnalysisWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)
    status_changed = Signal(str)

    def __init__(
            self,
            controller,
            log_file: str,
            vehicle,
            channel,
        ):
        super().__init__()
        self._controller = controller
        self._log_file = log_file
        self._vehicle = vehicle
        self._channel = channel

    @Slot()
    def run(self):
        try:
            result = self._controller.fn_run(
                log_file=self._log_file,
                vehicle=self._vehicle,
                channel=self._channel,
                logger=self.status_changed.emit,
            )
        except Exception as e:
            self.failed.emit(str(e))
            return

        self.finished.emit(result)
