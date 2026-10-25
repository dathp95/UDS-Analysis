import logging

from PySide6.QtCore import QEventLoop, QObject, QThread, QTimer, Qt, Signal, Slot

from services.can import CANDiscoveryError

LOG = logging.getLogger(__name__)


class CANDiscoveryWorker(QObject):
    completed = Signal(object)
    failed = Signal(object)
    finished = Signal()

    def __init__(self, service):
        super().__init__()
        self._service = service
        self.outcome = None

    @Slot()
    def run(self):
        try:
            if QThread.currentThread().isInterruptionRequested():
                self.outcome = (False, CANDiscoveryError("Vector discovery was cancelled during shutdown."))
                return
            self.outcome = (True, self._service.fn_refresh())
        except CANDiscoveryError as error:
            self.outcome = (False, error)
        except Exception as error:
            LOG.exception("Unexpected CAN discovery error")
            failure = CANDiscoveryError("Vector device discovery failed. Check the application log.")
            failure.__cause__ = error
            self.outcome = (False, failure)
        finally:
            if self.outcome[0]:
                self.completed.emit(self.outcome[1])
            else:
                self.failed.emit(self.outcome[1])
            self.finished.emit()


class CANDiscoveryTask(QObject):
    """Own native discovery until it stops, even if its tab is destroyed."""

    completed = Signal(object)
    failed = Signal(object)
    stopped = Signal()

    def __init__(self, service, parent):
        super().__init__(parent)
        self._service = service
        self._thread = None
        self._worker = None
        self._outcome = None
        self._closed = False

    @property
    def running(self):
        return self._thread is not None

    def start(self):
        if self._closed or self.running:
            return
        self._outcome = None
        self._thread = QThread(self)
        self._worker = CANDiscoveryWorker(self._service)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.completed.connect(self._record_result, Qt.DirectConnection)
        self._worker.failed.connect(self._record_error, Qt.DirectConnection)
        self._worker.finished.connect(self._thread.quit, Qt.DirectConnection)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._finish)
        self._thread.start()

    @Slot(object)
    def _record_result(self, devices):
        self._outcome = (True, devices)

    @Slot(object)
    def _record_error(self, error):
        self._outcome = (False, error)

    @Slot()
    def _finish(self):
        # finished can precede native thread-local/deferred-delete teardown.
        # Keep Python wrappers alive until that teardown actually completes.
        if not self._thread.wait(0):
            QTimer.singleShot(1, self._finish)
            return
        self._thread.deleteLater()
        # Only Python data is recorded directly; all public delivery runs on GUI.
        outcome = self._outcome
        self._worker = None
        self._thread = None
        self._outcome = None
        self.stopped.emit()
        if self._closed:
            self.deleteLater()
            return
        if outcome is None:
            self.failed.emit(CANDiscoveryError("Vector discovery finished without a result."))
        elif outcome[0]:
            self.completed.emit(outcome[1])
        else:
            self.failed.emit(outcome[1])

    @Slot()
    def dispose(self):
        if self._closed:
            return
        self._closed = True
        if self.running:
            self._thread.requestInterruption()
        else:
            self.deleteLater()

    @Slot()
    def shutdown(self):
        self.dispose()
        if self.running:
            loop = QEventLoop()
            self.stopped.connect(loop.quit)
            loop.exec()
            self.stopped.disconnect(loop.quit)
