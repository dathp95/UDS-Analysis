from dataclasses import replace

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox
from core.diagnostic_request import DiagnosticSettings,DiagnosticValidationError
from services.can import CANConnectionState
from services.can.ecu_diagnostic_resolver import resolve_request


class CanDiagnosticController(QObject):
    """Manual row intent -> frozen canonical request -> GUI-only real results."""
    def __init__(self,panel,monitor,service,task,parent=None):
        super().__init__(parent)
        self.panel,self.monitor,self.service,self.task=panel,monitor,service,task
        self.settings=DiagnosticSettings()
        self.generation=0
        self._active=None
        self._preparing=False
        self._closed=False
        panel.row_send_requested.connect(self.send_row)
        panel.document_changed.connect(self.invalidate)
        panel.sequence_modified.connect(self.invalidate)
        panel.vehicle_configuration_changed.connect(self.invalidate)
        task.diagnostic_finished.connect(self._result)
        task.frame_batch.connect(self._frames)
        task.monitoring_changed.connect(lambda active:monitor.set_monitoring_state('Monitoring' if active else 'Stopped'))
        task.completed.connect(self._state)
        task.failed.connect(self._state)
        task.started.connect(self._state)
        task.connection_fault.connect(self._state)
        self.destroyed.connect(task.cancel_diagnostic)
        self._state()

    def _state(self,*_):
        self.panel.set_send_available(not self._closed and self.service.snapshot.state == CANConnectionState.CONNECTED
                                      and self.task.alive and not self.task.running)

    def send_row(self,key):
        if self._closed or self._preparing or self._active is not None or self.task.diagnostic_busy:
            return
        step=self.panel.step_for_id(key)
        if step is None: return
        generation=self.generation
        vehicle=self.panel.fn_current_vehicle()
        self._preparing=True
        try:
            if self.service.snapshot.state != CANConnectionState.CONNECTED or self.task.running:
                raise DiagnosticValidationError('Connect the selected Vector channel before sending.')
            request=resolve_request(self.panel._vehicle_service,vehicle,step,key,generation,self.settings)
            if request.requires_confirmation:
                answer=QMessageBox.question(self.panel,'Confirm one state-changing diagnostic request',
                    f'Vehicle: {vehicle}\nECU: {request.ecu_name}\nTX: 0x{request.tx_id:03X}, RX: 0x{request.rx_id:03X}\n'
                    f'Payload: {request.uds_payload.hex(" ").upper()}\nSend this one request on the test bench?',
                    QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
                if answer != QMessageBox.Yes:
                    self.panel.show_notice('Request not sent: confirmation declined.');return
                request=replace(request,confirmed=True)
            if generation != self.generation or self.panel.step_for_id(key) != step or self.panel.fn_current_vehicle() != vehicle:
                raise DiagnosticValidationError('Document/Vehicle changed; request was not sent.')
            if not self.task.submit_diagnostic(request):
                raise DiagnosticValidationError('The CAN owner is busy or disconnected; request was not sent.')
            self._active=request
            self.panel.set_request_busy(True)
            self.panel.set_step_running(key)
            self.panel.show_notice('One manual UDS request running. TX indicates driver acceptance, not ECU acknowledgement.')
        except (ValueError,RuntimeError) as error:
            self.panel.show_notice(str(error))
            self.panel.set_step_result(key,'','Error',str(error))
        finally:
            self._preparing=False

    def invalidate(self,*_):
        self.generation+=1
        if self._active is not None: self.task.cancel_diagnostic()

    def _result(self,result):
        if self._active is None or result.request.transaction_id != self._active.transaction_id:
            return
        self._active=None
        self.panel.set_request_busy(False)
        self._state()
        if self._closed: return
        request=result.request
        if request.generation != self.generation or self.panel.step_for_id(request.step_id) is None:
            return
        payload=result.response_payload.hex(' ').upper() if result.response_payload is not None else ''
        detail=f'{result.detail} RT: {result.elapsed_s:.3f} s; NRC 0x78 count: {result.pending_count}.'
        self.panel.set_step_result(request.step_id,payload,result.outcome.value,detail)
        self.panel.show_notice(detail)

    def _frames(self,frames,dropped):
        if self._closed: return
        self.monitor.append_frame_batch(frames,dropped=dropped)

    def close(self):
        self._closed=True
        self.task.cancel_diagnostic()
