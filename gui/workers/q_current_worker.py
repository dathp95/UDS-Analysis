from collections.abc import Callable

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot


class QCurrentWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, operation: Callable[[], object]):
        super().__init__()
        self._operation = operation

    @Slot()
    def run(self):
        try:
            result = self._operation()
        except Exception as error:
            self.failed.emit(str(error))
            return
        self.finished.emit(result)


class QCurrentTaskRunner(QObject):
    """Deliver results on the GUI thread only after the worker has stopped."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self._thread = None
        self._worker = None
        self._outcome = None

    @property
    def running(self):
        return self._thread is not None

    def start(self, operation: Callable[[], object]):
        if self.running:
            raise RuntimeError("A Q Current operation is already running.")
        self._outcome = None
        self._thread = QThread(self)
        self._worker = QCurrentWorker(operation)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(
            self._record_result,
            Qt.DirectConnection,
        )
        self._worker.failed.connect(
            self._record_error,
            Qt.DirectConnection,
        )
        self._worker.finished.connect(self._thread.quit, Qt.DirectConnection)
        self._worker.failed.connect(self._thread.quit, Qt.DirectConnection)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._finish)
        self._thread.start()

    @Slot(object)
    def _record_result(self, result):
        self._outcome = (True, result)

    @Slot(str)
    def _record_error(self, message):
        self._outcome = (False, message)

    @Slot()
    def _finish(self):
        outcome = self._outcome

        self._thread = None
        self._worker = None
        self._outcome = None

        if outcome is None:
            self.failed.emit(
                "Q Current worker finished without a result."
            )
            return

        success, result = outcome

        if success:
            self.finished.emit(result)
        else:
            self.failed.emit(result)

    @Slot()
    def wait(self):
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
