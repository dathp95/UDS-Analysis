from dataclasses import replace

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QMessageBox
from core.diagnostic_request import DiagnosticSettings,DiagnosticValidationError
from services.can import CANConnectionState
from services.can.ecu_diagnostic_resolver import resolve_request
from services.can.security_access_session import SecurityAccessSession, SecurityAccessBlocked

class CanDiagnosticController(QObject):
    """Manual row intent -> frozen canonical request -> GUI-only real results."""
    security_status_changed = Signal(str)

    def __init__(self,panel,monitor,service,task,parent=None):
        super().__init__(parent)
        self.panel,self.monitor,self.service,self.task=panel,monitor,service,task
        self.settings=DiagnosticSettings()
        self.generation=0
        self._active=None
        self._preparing=False
        self._closed=False
        self.security_session=SecurityAccessSession()
        self._security_connection_id=''
        self._session_epoch=0
        self._security_status=''
        self._security_timer=QTimer(self)
        self._security_timer.setInterval(250)
        self._security_timer.timeout.connect(self._refresh_security_status)
        self._security_timer.start()
        panel.row_send_requested.connect(self.send_row)
        panel.document_changed.connect(self.invalidate)
        panel.sequence_modified.connect(self.invalidate)
        panel.vehicle_configuration_changed.connect(self._vehicle_configuration_changed)
        panel.row_selected.connect(self._security_selection_changed)
        panel.vehicle_resources_changed.connect(self._invalidate_security)
        task.diagnostic_finished.connect(self._result)
        task.frame_batch.connect(self._frames)
        task.monitoring_changed.connect(lambda active:monitor.set_monitoring_state('Monitoring' if active else 'Stopped'))
        task.completed.connect(self._state)
        task.failed.connect(self._state)
        task.started.connect(self._connection_started)
        task.connection_fault.connect(self._state)
        self.destroyed.connect(task.cancel_diagnostic)
        self._state()

    def _state(self,*_):
        connection_id=self._connection_identity()
        if connection_id != self._security_connection_id:
            self._invalidate_security()
            self._session_epoch+=1
            self._security_connection_id=connection_id
        self.panel.set_send_available(not self._closed and self.service.snapshot.state == CANConnectionState.CONNECTED
                                      and self.task.alive and not self.task.running)

    def _connection_identity(self):
        # Discovery-only service adapters can present the tab without capture.
        # An absent identity disables SecurityAccess; never invent a generation.
        value=getattr(self.service,'capture_session_id',None)
        return value if isinstance(value,str) else ''

    def _refresh_security_status(self):
        status=self.security_session.status_text
        if status != self._security_status:
            self._security_status=status
            self.security_status_changed.emit(status)

    def _invalidate_security(self,*_):
        self.security_session.invalidate()
        self._refresh_security_status()

    def _security_selection_changed(self,*_):
        identity=self.security_session.identity
        step=self.panel.step_for_id(self.panel.selected_step_id())
        if identity is not None and (step is None or step.ecu != identity.ecu
                                     or self.panel.fn_current_vehicle() != identity.vehicle):
            self._invalidate_security()

    def _connection_started(self,*_):
        self._invalidate_security()
        self._session_epoch+=1
        self.service.fn_revoke_trusted_bench()
        self._state()

    def _vehicle_configuration_changed(self,*_):
        self.invalidate()
        self._state()

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
                authorized=self.service.fn_confirm_trusted_request(request)
                if authorized is not None: request=authorized
            if request.requires_confirmation and not request.confirmed:
                answer=QMessageBox.question(self.panel,'Confirm one state-changing diagnostic request',
                    f'Vehicle: {vehicle}\nECU: {request.ecu_name}\nTX: 0x{request.tx_id:03X}, RX: 0x{request.rx_id:03X}\n'
                    f'Payload: {request.uds_payload.hex(" ").upper()}\nSend this one request on the test bench?',
                    QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
                if answer != QMessageBox.Yes:
                    self.panel.show_notice('Request not sent: confirmation declined.');return
                request=replace(request,confirmed=True)
            if generation != self.generation or self.panel.step_for_id(key) != step or self.panel.fn_current_vehicle() != vehicle:
                raise DiagnosticValidationError('Document/Vehicle changed; request was not sent.')
            identity=self.security_session.identity
            if identity is not None and (request.vehicle_name,request.ecu_name,request.tx_id,request.rx_id) != (
                    identity.vehicle,identity.ecu,identity.tx_id,identity.rx_id):
                self._invalidate_security()
            if request.uds_payload[:1] == b'\x10':
                self._session_epoch+=1
                self._invalidate_security()
            if request.uds_payload == b'\x27\x01':
                self.security_session.start(request,self._connection_identity(),self._session_epoch)
                self._refresh_security_status()
            if not self.task.submit_diagnostic(request):
                raise DiagnosticValidationError('The CAN owner is busy or disconnected; request was not sent.')
            self._active=request
            self.panel.set_request_busy(True)
            self.panel.set_step_running(key)
            self.panel.show_notice('One manual UDS request running. TX indicates driver acceptance, not ECU acknowledgement.')
        except (ValueError,RuntimeError) as error:
            self._invalidate_security()
            self.panel.show_notice(str(error))
            self.panel.set_step_result(key,'','Error',str(error))
        finally:
            self._preparing=False
            self._state()

    def invalidate(self,*_):
        self.generation+=1
        self._invalidate_security()
        if self._active is not None:
            self.task.cancel_diagnostic()
            self.panel.invalidate_step_result(self._active.step_id)


    def _result(self, result):
        # 1. Ignore responses that do not belong
        # to the currently active transaction.
        if (
            self._active is None
            or result.request.transaction_id
            != self._active.transaction_id
        ):
            return

        self._active = None
        self.panel.set_request_busy(False)
        self._state()

        if self._closed:
            return

        request = result.request

        # 2. Prevent stale results after switching
        # Vehicle, sequence, or editing steps.
        if (
            request.generation != self.generation
            or self.panel.step_for_id(request.step_id) is None
        ):
            return

        # 3. Preserve existing UDS result display.
        payload = (
            result.response_payload.hex(" ").upper()
            if result.response_payload is not None
            else ""
        )

        detail = (
            f"{result.detail} "
            f"RT: {result.elapsed_s:.3f} s; "
            f"NRC 0x78 count: {result.pending_count}."
        )

        self.panel.set_step_result(
            request.step_id,
            payload,
            result.outcome.value,
            detail,
        )

        # 4. Default notice for all diagnostic services.
        notice = detail

        # A seed belongs to this exact connection/document/session generation.
        if request.uds_payload == b"\x27\x01":
            try:
                self.security_session.receive(result,self._connection_identity(),self._session_epoch)
            except SecurityAccessBlocked:
                self._invalidate_security()
            self._refresh_security_status()
            notice = self.security_session.status_text+' '+detail

        # 6. Display one final notice.
        self.panel.show_notice(notice)


    def _frames(self,frames,dropped):
        if self._closed: return
        self.monitor.append_frame_batch(frames,dropped=dropped)

    def close(self):
        self._closed=True
        self._security_timer.stop()
        self._invalidate_security()
        self.service.fn_revoke_trusted_bench()
        self.task.cancel_diagnostic()
