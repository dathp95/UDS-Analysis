"""Bounded I/O pump, child of the existing native connection owner worker."""
import logging
import time

from PySide6.QtCore import QObject,QTimer,Qt,Signal,Slot
from core.diagnostic_request import DiagnosticResult,DiagnosticOutcome as Outcome
from services.can.can_connection import CANIoError

LOG=logging.getLogger(__name__)


class CanDiagnosticSession(QObject):
    finished=Signal(object)
    raw_frames=Signal(object)
    connection_fault=Signal(object)
    monitoring_changed=Signal(bool)
    capture_failed=Signal(str)

    def __init__(self,service,parent):
        super().__init__(parent)
        self.service=service
        self.request=None
        self.client=None
        self.cancelled=None
        self._frames=[]
        self._leased=False
        self.monitoring=False
        self.capture_sink=None
        self.timer=QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.setInterval(2)
        self.timer.timeout.connect(self._pump)

    def start_monitoring(self):
        self.monitoring=True
        self.timer.start()
        self.monitoring_changed.emit(True)

    def stop_monitoring(self):
        self.timer.stop()
        self.monitoring=False
        self.cancel()
        self._publish()
        self.monitoring_changed.emit(False)

    def _capture(self,frame):
        if self.capture_sink is not None: self.capture_sink(frame)
        self._frames.append(frame)

    def start(self,request,cancelled):
        if self.request is not None:
            self.finished.emit(DiagnosticResult(request,Outcome.ERROR,detail='A diagnostic request is already running.'))
            return
        self.request=request
        self.cancelled=cancelled
        self.started=time.monotonic()
        try:
            # Import lazily: missing optional transport dependency never breaks
            # discovery/connection or application startup, and sends no frame.
            from services.can.diagnostic_client import DiagnosticClient
            self._client_class=DiagnosticClient
            self.service.fn_begin_diagnostic(request)
            self._leased=True
            if not self.monitoring: self.start_monitoring()
        except Exception as error:
            LOG.exception('Cannot start diagnostic transport')
            message='can-isotp 2.0.7 is required; install requirements.txt.' if isinstance(error,ImportError) else str(error)
            self._finish(DiagnosticResult(request,Outcome.ERROR,detail=message))

    def _send(self,can_id,data):
        frame=self.service.fn_send_diagnostic_frame(can_id,data)
        self._capture(frame)

    def _publish(self):
        if self._frames:
            self.raw_frames.emit(tuple(self._frames))
            self._frames.clear()

    @Slot()
    def _pump(self):
        if not self.monitoring: return
        try:
            if self.request is None:
                for _ in range(32):
                    frame=self.service.fn_receive_capture_frame()
                    if frame is None: break
                    self._capture(frame)
                return
            if self.cancelled.is_set():
                self.cancel();return
            if time.monotonic()-self.started >= self.request.settings.total_s:
                result=self.client.finish(Outcome.TIMEOUT,detail='Maximum transaction duration exceeded.') if self.client else DiagnosticResult(self.request,Outcome.TIMEOUT,detail='RX backlog did not clear within the transaction budget.')
                self._finish(result);return
            # Drain old driver queue before transmitting; cooperative and bounded,
            # so Disconnect is still serviced even with a saturated CAN channel.
            if self.client is None:
                for _ in range(32):
                    if self.cancelled.is_set(): self.cancel();return
                    frame=self.service.fn_receive_diagnostic_frame()
                    if frame is None:
                        self.client=self._client_class(self.request,self._send,self.cancelled)
                        self._wall_start=time.time()
                        break
                    self._capture(frame)
                if self.client is None:
                    if time.monotonic()-self.started >= min(2.0,self.request.settings.total_s):
                        self._finish(DiagnosticResult(self.request,Outcome.ERROR,detail='RX backlog did not clear; no request was sent. Retry after the channel recovers.'))
                    return
            self.client.poll()  # Send the request before handling its response.
            for _ in range(32):
                if self.client.result is not None: break
                if self.cancelled.is_set(): self.cancel();return
                frame=self.service.fn_receive_diagnostic_frame()
                if frame is None: break
                self._capture(frame)
                # Preserve stale frames for monitor, but not for a new transaction.
                source_stamp=frame.source_timestamp_s if frame.timestamp_source.startswith('driver') else frame.wall_timestamp_s
                if source_stamp is None or source_stamp >= self._wall_start:
                    self.client.feed(frame)
                    self.client.poll()
            self.client.poll()
            if self.client.result is not None: self._finish(self.client.result)
        except CANIoError as error:
            self.capture_failed.emit(f'CAN capture stopped unexpectedly: {error}')
            LOG.exception('Native diagnostic I/O failed')
            result=(self.client.finish(Outcome.ERROR,detail=str(error)) if self.client else
                    DiagnosticResult(self.request,Outcome.ERROR,detail=str(error)) if self.request else None)
            self.timer.stop()
            self.monitoring=False
            self.monitoring_changed.emit(False)
            self._release()
            try: self.service.fn_transport_failed(error)
            except Exception: LOG.exception('Cleanup following diagnostic I/O error failed')
            self.connection_fault.emit(self.service.snapshot)
            if result is not None: self.finished.emit(result)
        except Exception as error:
            self.capture_failed.emit(f'CAN acquisition/processing failed: {error}')
            LOG.exception('Diagnostic processing failed')
            if self.request is not None:
                result=self.client.finish(Outcome.ERROR,detail=str(error)) if self.client else DiagnosticResult(self.request,Outcome.ERROR,detail=str(error))
                self._finish(result)
            else:
                self.timer.stop()
                self.monitoring=False
                self.monitoring_changed.emit(False)
                self.connection_fault.emit(self.service.snapshot)
        finally:
            self._publish()

    def _release(self):
        if self._leased:
            self.service.fn_end_diagnostic(self.request.transaction_id)
            self._leased=False
        self.request=None
        self.client=None
        self._publish()

    def _finish(self,result):
        self._release()
        self.finished.emit(result)

    def cancel(self):
        if self.request is None: return
        result=self.client.cancel() if self.client else DiagnosticResult(self.request,Outcome.CANCELLED,detail='Diagnostic request cancelled before TX.')
        self._finish(result)
