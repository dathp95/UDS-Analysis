import logging
from enum import Enum
from collections import deque
from threading import Event,Lock

from PySide6.QtCore import QEventLoop, QObject, QThread, QTimer, Qt, Signal, Slot

from services.can import CANConnectionError, CANConnectionState
from gui.workers.can_diagnostic_session import CanDiagnosticSession
from services.can.blf_recording_service import BlfRecordingService

LOG = logging.getLogger(__name__)


class CANConnectionOperation(Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"


class CANConnectionWorker(QObject):
    completed = Signal(int, object, object)
    failed = Signal(int, object, object)
    stopped = Signal()
    diagnostic_finished=Signal(object)
    raw_frames=Signal(object)
    connection_fault=Signal(object)
    monitoring_changed=Signal(bool)
    recording_start_finished=Signal(object)

    def __init__(self, service, recorder=None):
        super().__init__()
        self._service = service
        self.recorder=recorder if recorder is not None else BlfRecordingService()
        self.session=CanDiagnosticSession(service,self)
        self.session.capture_sink=self.recorder.offer
        self.session.capture_failed.connect(self.recorder.stop)
        self.session.finished.connect(self.diagnostic_finished)
        self.session.raw_frames.connect(self.raw_frames)
        self.session.connection_fault.connect(self._capture_fault)
        self.session.monitoring_changed.connect(self.monitoring_changed)
        self._finalize_timer=QTimer(self)
        self._finalize_timer.setInterval(25)
        self._finalize_timer.timeout.connect(self._finish_recording)
        self._after_finalize=None

    def _capture_fault(self,snapshot):
        self.recorder.stop('CAN capture stopped unexpectedly: '+(snapshot.error or 'receive pump failed'))
        self.connection_fault.emit(snapshot)

    def _when_finalized(self,callback):
        self._after_finalize=callback
        self._finish_recording()

    def _finish_recording(self):
        if self.recorder.snapshot.busy:
            self._finalize_timer.start()
            return
        self._finalize_timer.stop()
        callback,self._after_finalize=self._after_finalize,None
        if callback is not None: callback()

    @Slot(object,object)
    def diagnostic(self,request,cancelled):
        self.session.start(request,cancelled)

    @Slot(object,bool,str)
    def start_recording(self,path,overwrite,session_id):
        try:
            if (not self.session.monitoring or self._service.snapshot.state != CANConnectionState.CONNECTED
                    or session_id != self._service.capture_session_id):
                raise RuntimeError('CAN session changed; BLF recording was not started.')
            self.recorder.start(path,session_id,overwrite=overwrite)
        except (OSError,RuntimeError,ValueError) as error:
            self.recording_start_finished.emit(str(error))
        else:
            self.recording_start_finished.emit(None)

    @Slot()
    def stop_recording(self):
        self.recorder.stop()

    @Slot(int, object, object)
    def execute(self, token, operation, config):
        try:
            if operation == CANConnectionOperation.CONNECT:
                self._service.fn_connect(config)
                self.session.start_monitoring()
            elif operation == CANConnectionOperation.DISCONNECT:
                self.session.stop_monitoring()
                self.recorder.stop()
                self._service.fn_disconnect()
            else:
                raise CANConnectionError("Unknown CAN connection operation.")
        except Exception as error:
            LOG.exception("CAN connection operation failed")
            self.failed.emit(token, operation, error)
        else:
            snapshot=self._service.snapshot
            if operation==CANConnectionOperation.DISCONNECT:
                self._when_finalized(lambda:self.completed.emit(token,operation,snapshot))
            else:
                self.completed.emit(token,operation,snapshot)

    @Slot()
    def close(self):
        self.session.stop_monitoring()
        self.recorder.stop()
        try:
            if self._service.snapshot.state in (CANConnectionState.CONNECTED, CANConnectionState.ERROR):
                self._service.fn_disconnect()
        except Exception:
            # Service keeps RECOVERY_REQUIRED and the native owner reference.
            LOG.exception("CAN connection cleanup during shutdown failed")
        finally:
            self._when_finalized(self.stopped.emit)


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
    _diagnostic_request=Signal(object,object)
    diagnostic_finished=Signal(object)
    frame_batch=Signal(object,int)
    connection_fault=Signal(object)
    monitoring_changed=Signal(bool)
    _recording_start=Signal(object,bool,str)
    _recording_stop=Signal()
    recording_start_finished=Signal(object)

    def __init__(self, service, parent):
        super().__init__(parent)
        self._service = service
        self.recorder=BlfRecordingService()
        self._thread = None
        self._worker = None
        self._busy = False
        self._closed = False
        self._token = 0
        self._diagnostic_id=None
        self._cancel_event=Event()
        self._frames=deque(maxlen=4096)
        self._frame_lock=Lock()
        self._frame_drops=0
        self.monitoring=False
        self.recording_start_pending=False
        self._frame_timer=QTimer(self)
        self._frame_timer.setInterval(75)
        self._frame_timer.timeout.connect(self._drain_frames)

    @property
    def diagnostic_busy(self): return self._diagnostic_id is not None

    def submit_diagnostic(self,request):
        if (self._closed or self.running or self.diagnostic_busy or not self.alive
                or self._service.snapshot.state != CANConnectionState.CONNECTED):
            return False
        self._diagnostic_id=request.transaction_id
        self._cancel_event=Event()
        self._frame_timer.start()
        self._diagnostic_request.emit(request,self._cancel_event)
        return True

    def cancel_diagnostic(self):
        self._cancel_event.set()  # Cooperative check before every pump and ISO-TP TX.

    def start_recording(self,path,*,overwrite=False):
        if self._closed or self.running or self.recording_start_pending or self.recorder.snapshot.busy or not self.monitoring or self._service.snapshot.state != CANConnectionState.CONNECTED:
            raise RuntimeError('Connect and start CAN monitoring before recording.')
        self.recording_start_pending=True
        self._recording_start.emit(path,overwrite,self._service.capture_session_id)

    @Slot(object)
    def _recording_started(self,error):
        self.recording_start_pending=False
        if not self._closed: self.recording_start_finished.emit(error)

    def stop_recording(self):
        self._recording_stop.emit()

    @Slot(object)
    def _record_frames(self,frames):
        # DirectConnection: Python data/lock only, never QWidget/QTimer access.
        with self._frame_lock:
            for frame in frames:
                if len(self._frames) == self._frames.maxlen: self._frame_drops+=1
                self._frames.append(frame)

    @Slot()
    def _drain_frames(self):
        with self._frame_lock:
            frames=tuple(self._frames.popleft() for _ in range(min(1024,len(self._frames))))
            dropped=self._frame_drops
            self._frame_drops=0
            remaining=bool(self._frames)
        if not self._closed and (frames or dropped): self.frame_batch.emit(frames,dropped)
        if not remaining and not self.diagnostic_busy and not self.monitoring: self._frame_timer.stop()

    @Slot(bool)
    def _monitor_state(self,active):
        self.monitoring=active
        if active and not self._closed: self._frame_timer.start()
        else: self._drain_frames()
        if not self._closed: self.monitoring_changed.emit(active)

    @Slot(object)
    def _diagnostic_done(self,result):
        if result.request.transaction_id != self._diagnostic_id: return
        self._diagnostic_id=None
        self._drain_frames()
        if not self._closed: self.diagnostic_finished.emit(result)

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
            self._worker = CANConnectionWorker(self._service,self.recorder)
            self._worker.moveToThread(self._thread)
            self._request.connect(self._worker.execute, Qt.QueuedConnection)
            self._close_request.connect(self._worker.close, Qt.QueuedConnection)
            self._worker.completed.connect(self._complete)
            self._worker.failed.connect(self._fail)
            self._diagnostic_request.connect(self._worker.diagnostic,Qt.QueuedConnection)
            self._worker.diagnostic_finished.connect(self._diagnostic_done)
            self._worker.raw_frames.connect(self._record_frames,Qt.DirectConnection)
            self._worker.connection_fault.connect(self.connection_fault)
            self._worker.monitoring_changed.connect(self._monitor_state)
            self._recording_start.connect(self._worker.start_recording,Qt.QueuedConnection)
            self._worker.recording_start_finished.connect(self._recording_started)
            self._recording_stop.connect(self._worker.stop_recording,Qt.QueuedConnection)
            self._worker.stopped.connect(self._thread.quit, Qt.DirectConnection)
            self._thread.finished.connect(self._worker.deleteLater)
            self._thread.finished.connect(self._thread_stopped)
            self._thread.start()
        self._busy = True
        if operation == CANConnectionOperation.DISCONNECT: self.cancel_diagnostic()
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
        self.cancel_diagnostic()
        self._frame_timer.stop()
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
        self._diagnostic_id=None
        self._frame_timer.stop()
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
