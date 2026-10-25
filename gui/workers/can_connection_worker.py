import logging
from enum import Enum

from PySide6.QtCore import QEventLoop, QObject, QThread, QTimer, Qt, Signal, Slot

from services.can import CANConnectionError, CANConnectionState

LOG = logging.getLogger(__name__)


class CANConnectionOperation(Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"


class CANConnectionWorker(QObject):
    completed = Signal(int, object, object)
    failed = Signal(int, object, object)
    stopped = Signal()

    def __init__(self, service):
        super().__init__()
        self._service = service

    @Slot(int, object, object)
    def execute(self, token, operation, config):
        try:
            if operation == CANConnectionOperation.CONNECT:
                self._service.fn_connect(config)
            elif operation == CANConnectionOperation.DISCONNECT:
                self._service.fn_disconnect()
            else:
                raise CANConnectionError("Unknown CAN connection operation.")
        except Exception as error:
            LOG.exception("CAN connection operation failed")
            self.failed.emit(token, operation, error)
        else:
            self.completed.emit(token, operation, self._service.snapshot)

    @Slot()
    def close(self):
        try:
            if self._service.snapshot.state in (CANConnectionState.CONNECTED, CANConnectionState.ERROR):
                self._service.fn_disconnect()
        except Exception:
            # Service keeps RECOVERY_REQUIRED and the native owner reference.
            LOG.exception("CAN connection cleanup during shutdown failed")
        finally:
            self.stopped.emit()


class CANConnectionTask(QObject):
    """One lazy owner thread for open/close/reconnect, never one thread per call.

    Source: https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html
    """
    started = Signal(object)
    completed = Signal(object, object)
    failed = Signal(object, object)
    finished = Signal(object)
    stopped = Signal()
    _request = Signal(int, object, object)
    _close_request = Signal()

    def __init__(self, service, parent):
        super().__init__(parent)
        self._service = service
        self._thread = None
        self._worker = None
        self._busy = False
        self._closed = False
        self._token = 0

    @property
    def running(self):
        return self._busy

    @property
    def alive(self):
        return self._thread is not None

    def start(self, operation, config=None):
        if self._closed or self._busy:
            return False
        if self._thread is None:
            self._thread = QThread(self)
            self._worker = CANConnectionWorker(self._service)
            self._worker.moveToThread(self._thread)
            self._request.connect(self._worker.execute, Qt.QueuedConnection)
            self._close_request.connect(self._worker.close, Qt.QueuedConnection)
            self._worker.completed.connect(self._complete)
            self._worker.failed.connect(self._fail)
            self._worker.stopped.connect(self._thread.quit, Qt.DirectConnection)
            self._thread.finished.connect(self._worker.deleteLater)
            self._thread.finished.connect(self._thread_stopped)
            self._thread.start()
        self._busy = True
        self._token += 1
        self.started.emit(operation)
        self._request.emit(self._token, operation, config)
        return True

    @Slot(int, object, object)
    def _complete(self, token, operation, snapshot):
        if token != self._token or self._closed:
            return
        self._busy = False
        self.completed.emit(operation, snapshot)
        self.finished.emit(operation)

    @Slot(int, object, object)
    def _fail(self, token, operation, error):
        if token != self._token or self._closed:
            return
        self._busy = False
        self.failed.emit(operation, error)
        self.finished.emit(operation)

    @Slot()
    def dispose(self):
        if self._closed:
            return
        self._closed = True
        if self._thread is not None:
            # Queued after any in-flight call, on the same native owner thread.
            self._close_request.emit()
        else:
            self.stopped.emit()

    @Slot()
    def _thread_stopped(self):
        if not self._thread.wait(0):
            QTimer.singleShot(1, self._thread_stopped)
            return
        self._thread.deleteLater()
        self._thread = None
        self._worker = None
        self._busy = False
        self.stopped.emit()

    @Slot()
    def shutdown(self):
        self.dispose()
        if self.alive:
            # aboutToQuit fallback: keep dispatching events during native cleanup,
            # never use unbounded QThread.wait() on the GUI or destroy its owner.
            loop = QEventLoop()
            self.stopped.connect(loop.quit)
            loop.exec()
            self.stopped.disconnect(loop.quit)
