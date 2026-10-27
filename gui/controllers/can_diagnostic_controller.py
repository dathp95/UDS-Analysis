from dataclasses import replace

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox
from core.diagnostic_request import DiagnosticSettings,DiagnosticValidationError
from services.can import CANConnectionState
from services.can.ecu_diagnostic_resolver import resolve_request
from core.diagnostic_request import DiagnosticOutcome
from services.can.security_seed_parser import (
    parse_security_seed,
    SecuritySeedError,
)

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
        panel.vehicle_configuration_changed.connect(self._vehicle_configuration_changed)
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
        self.panel.set_send_available(not self._closed and self.service.snapshot.state == CANConnectionState.CONNECTED
                                      and self.task.alive and not self.task.running)

    def _connection_started(self,*_):
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
            self._state()

    def invalidate(self,*_):
        self.generation+=1
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

        # 5. Handle SecurityAccess Request Seed (27 01).
        if (
            request.uds_payload == b"\x27\x01"
            and result.outcome in (
                DiagnosticOutcome.PASSED,
                DiagnosticOutcome.NOT_EVALUATED,
            )
            and result.response_payload is not None
        ):
            try:
                parsed = parse_security_seed(
                    request_payload=request.uds_payload,
                    response_payload=result.response_payload,
                )

                # Seed exists in memory for this completed result.
                # Do not persist it or print its value.
                notice = (
                    "SecurityAccess 27 01 successful. "
                    f"Seed length: {len(parsed.seed)} bytes. "
                    "Key calculation is not enabled yet."
                )

            except SecuritySeedError as error:
                notice = (
                    f"SecurityAccess seed validation failed: "
                    f"{error}"
                )

        # 6. Display one final notice.
        self.panel.show_notice(notice)


    def _frames(self,frames,dropped):
        if self._closed: return
        self.monitor.append_frame_batch(frames,dropped=dropped)

    def close(self):
        self._closed=True
        self.service.fn_revoke_trusted_bench()
        self.task.cancel_diagnostic()
