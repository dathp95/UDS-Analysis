from __future__ import annotations

from numbers import Integral
from threading import Lock, RLock, get_ident
from core.diagnostic_request import validate_send_policy, DiagnosticValidationError, TrustedBenchAuthorization, DiagnosticCancelled
from dataclasses import replace
from uuid import uuid4
import logging

from services.can.can_config import CANConfig
from core.bench_authorization import BenchAuthorizationContext
from services.can.can_connection import CANConnectionError, CANConnectionSnapshot, CANConnectionState as State
from services.can.can_device import CANChannelInfo, CANDeviceInfo, CANDiscoveryError
from services.can.vector_backend import VectorBackend

LOG = logging.getLogger(__name__)


SUPPORTED_BITRATES = (
    125000,
    250000,
    500000,
    1000000,
)


class CANValidationError(ValueError):
    pass


class CANService:

    def __init__(self, backend=None):
        self._backend = backend if backend is not None else VectorBackend()
        self._operation_lock = Lock()
        self._state_lock = RLock()
        # Separate from snapshot/state reads: only bench TX and revocation
        # serialize here. Never hold the GUI-visible state lock across I/O.
        self._bench_tx_lock = RLock()
        self._snapshot = CANConnectionSnapshot()
        self._diagnostic_request = None
        self._diagnostic_owner = None
        self._trusted_bench = None
        self._bench_context = None
        self._bench_revision = 0
        from services.can.hmac_sha1_provider import ProviderVerificationGate
        from core.security_submission import SubmissionAuthority
        self.security_gate=ProviderVerificationGate(simulator=self.is_simulator)
        self._security_authority=SubmissionAuthority(self.security_gate.validate)
        self._security_epoch=0
        self._uds_session=None
        self._uds_session_target=None
        self._auto_context = None
        self._auto_seed_admitted = False

    def _resolve_ecu_dll_path(self, vehicle, ecu):
        vs = getattr(self, 'vehicle_service', None)
        if vs is None:
            try:
                from services.vehicle_service import VehicleService
                vs = VehicleService()
                self.vehicle_service = vs
            except Exception:
                vs = None
        if vs is not None:
            try:
                metadata = vs.resolve_ecu_dll_resource(vehicle, ecu)
                if metadata.configurable and (metadata.machine == 'x86' or metadata.has_generate_key_ex or 'GenerateKeyEx' in metadata.exports):
                    from pathlib import Path
                    p = Path(metadata.path)
                    if p.is_file():
                        return str(p.resolve())
            except Exception:
                pass
        from pathlib import Path
        candidate = Path(f'config/vehicles/{vehicle}/resources/dll/{ecu}/{ecu}.dll')
        if candidate.is_file():
            return str(candidate.resolve())
        ecu_dir = Path(f'config/vehicles/{vehicle}/resources/dll/{ecu}')
        if ecu_dir.is_dir():
            for dll_file in ecu_dir.glob('*.dll'):
                if dll_file.is_file():
                    return str(dll_file.resolve())
        return None

    def begin_auto_security(self, request):
        """Reserve a target-scoped two-transaction SecurityAccess workflow."""
        from services.can.auto_security_access import AutoSecurityAccessL1
        with self._state_lock:
            subfunc = request.uds_payload[1] if len(request.uds_payload) > 1 else 1
            provider = self.security_provider(request.vehicle_name, request.ecu_name, subfunction=subfunc)
            is_real = getattr(getattr(provider, '_proof', None), 'verified_real', False)
            if not self.is_simulator and not is_real:
                raise DiagnosticValidationError('Physical Auto L1 blocked: real provider ABI/offline verification and scoped workflow authorization required.')
            if self._auto_context is not None or self._diagnostic_request is not None:
                raise DiagnosticValidationError('A diagnostic workflow is already running.')
            if not self.security_ready_for(request):
                raise DiagnosticValidationError('Auto L1 requires an authorized bench and confirmed Extended session for this ECU.')
            if provider is None:
                raise DiagnosticValidationError('Auto L1 blocked: no verified Seed-Key provider for this ECU.')
            flow = AutoSecurityAccessL1(request)
            self._auto_context = (flow, self.capture_session_id, self._security_epoch,
                self.trusted_bench.authorization_id, provider, self.security_gate)
            self._auto_seed_admitted = False
            return flow

    def _check_auto_security(self, flow):
        context = self._auto_context
        if context is None or context[0] is not flow:
            raise DiagnosticValidationError('Auto L1 workflow was revoked.')
        _, connection, epoch, authorization, provider, gate = context
        request = flow.seed_request
        grant = self.trusted_bench
        is_real = getattr(getattr(provider, '_proof', None), 'verified_real', False)
        if (flow.expired or (not self.is_simulator and not is_real) or not self.security_ready_for(request) or grant is None
                or (connection, epoch, authorization) !=
                   (self.capture_session_id, self._security_epoch, grant.authorization_id)
                or gate is not self.security_gate
                or provider is not self.security_provider(request.vehicle_name, request.ecu_name, subfunction=flow.subfunction)):
            raise DiagnosticValidationError('Auto L1 target, provider, connection or bench authorization changed.')

    def auto_provider(self, flow):
        with self._state_lock:
            self._check_auto_security(flow)
            return self._auto_context[4], self._auto_context[5]

    def prepare_auto_submission(self, flow, session, session_epoch):
        with self._bench_tx_lock, self._state_lock:
            self._check_auto_security(flow)
            return self.prepare_security_submission(session, flow.seed_request, session_epoch, confirmed=True)

    def end_auto_security(self, flow):
        with self._state_lock:
            if self._auto_context is not None and self._auto_context[0] is flow:
                if flow.key_request is not None:
                    self._security_authority.retire(flow.key_request)
                self._auto_context = None

    def is_auto_request(self, request):
        context = self._auto_context
        return context is not None and request is not None and (
            request is context[0].seed_request or request is context[0].key_request)

    @property
    def is_simulator(self):
        from services.can.simulated_backend import SimulatedCANBackend
        return type(self._backend) is SimulatedCANBackend

    def security_provider(self, vehicle, ecu, subfunction=1):
        with self._state_lock:
            dll_path = self._resolve_ecu_dll_path(vehicle, ecu)
            prov = self.security_gate.provider(vehicle, ecu, subfunction=subfunction)
            if prov is not None and getattr(getattr(prov, '_proof', None), 'verified_real', False):
                if getattr(prov, '_dll_path', None) == dll_path or not dll_path:
                    return prov
            if dll_path:
                return self.security_gate.register_dll_provider(vehicle, ecu, dll_path, subfunction=subfunction)
            return prov

    @property
    def security_ready(self):
        return self.fn_is_connected() and self.trusted_bench is not None and self._uds_session==3

    @staticmethod
    def _security_target(request):
        return (request.vehicle_name, request.ecu_name, request.tx_id, request.rx_id)

    def security_ready_for(self, request):
        with self._state_lock:
            return self.security_ready and self._uds_session_target == self._security_target(request)

    def prepare_security_submission(self,session,request,session_epoch,*,confirmed):
        with self._bench_tx_lock,self._state_lock:
            grant=self.trusted_bench
            if not self.security_ready_for(request) or grant is None:
                raise DiagnosticValidationError('Authorized connected bench and confirmed Extended session are required.')
            return session.prepare_submission(request,self.capture_session_id,session_epoch,
                authorized=True,confirmed=confirmed,authority=self._security_authority,
                owner_epoch=self._security_epoch,authorization_id=grant.authorization_id)

    def _validate_key_submission(self,request,*,claim=False):
        grant=self.trusted_bench
        if grant is None or not self.security_ready_for(request):
            raise DiagnosticValidationError('SecurityAccess bench/session authorization expired.')
        method=self._security_authority.claim if claim else self._security_authority.check_active
        method(request,self.capture_session_id,self._security_epoch,grant.authorization_id,simulator=self.is_simulator)

    def fn_diagnostic_completed(self,result):
        from core.diagnostic_request import DiagnosticOutcome
        request=result.request
        if (self._diagnostic_request is request and len(request.uds_payload)>1 and request.uds_payload[:1]==b'\x10'
                and result.outcome in (DiagnosticOutcome.PASSED,DiagnosticOutcome.NOT_EVALUATED)
                and result.response_payload is not None and len(result.response_payload)>=2
                and result.response_payload[:2]==bytes((0x50,request.uds_payload[1]&0x7f))):
            self._uds_session=request.uds_payload[1]&0x7f
            self._uds_session_target=self._security_target(request)

    @property
    def snapshot(self) -> CANConnectionSnapshot:
        with self._state_lock:
            return self._snapshot

    def _transition(self, state, *, config=None, error="", rediscovery_required=False):
        allowed = {
            State.DISCONNECTED: {State.DISCONNECTED, State.CONNECTING, State.RECOVERY_REQUIRED},
            State.CONNECTING: {State.CONNECTED, State.ERROR, State.RECOVERY_REQUIRED},
            State.CONNECTED: {State.DISCONNECTING},
            State.DISCONNECTING: {State.DISCONNECTED, State.RECOVERY_REQUIRED},
            State.ERROR: {State.CONNECTING, State.DISCONNECTED, State.RECOVERY_REQUIRED},
            State.RECOVERY_REQUIRED: set(),
        }
        with self._state_lock:
            if state not in allowed[self._snapshot.state]:
                raise CANConnectionError("Invalid CAN connection state transition.")
            self._snapshot = CANConnectionSnapshot(state, config, error, rediscovery_required)
            if state != State.CONNECTED:
                self._auto_context = None
                self._security_authority.revoke_all()
                self._security_epoch+=1
                self._uds_session=None
                self._uds_session_target=None
                self._trusted_bench = None
                self._bench_context = None

    def fn_connect(self, config: CANConfig):
        self._validate_config(config)
        if not self._operation_lock.acquire(blocking=False):
            raise CANConnectionError("A CAN operation is already running.")
        try:
            if self.snapshot.state not in (State.DISCONNECTED, State.ERROR):
                raise CANConnectionError("Disconnect cleanly before opening another CAN connection.")
            if self.snapshot.rediscovery_required:
                raise CANConnectionError("Refresh Vector devices before connecting again.", rediscovery_required=True)
            with self._state_lock:
                self._transition(State.CONNECTING, config=config)
                self._bench_context = config.bench_context
                bench_revision = self._bench_revision
            try:
                self._backend.fn_open(config)
            except Exception as error:
                LOG.exception("CAN service connect failed")
                failure = error if isinstance(error, CANConnectionError) else CANConnectionError(
                    "Cannot initialize Vector CAN. Check the application log.", recovery_required=True)
                uncertain = failure.recovery_required or self._backend.fn_is_connected()
                self._transition(State.RECOVERY_REQUIRED if uncertain else State.ERROR,
                                 config=config if uncertain else None, error=str(failure),
                                 rediscovery_required=failure.rediscovery_required)
                if failure is error:
                    raise
                raise failure from error
            with self._state_lock:
                self._transition(State.CONNECTED, config=config)
                context = self._bench_context
                if bench_revision == self._bench_revision and context is not None and context.authorized:
                    connection_id = self.capture_session_id
                    if isinstance(connection_id,str) and connection_id:
                        self._trusted_bench = TrustedBenchAuthorization(uuid4().hex, connection_id, context.context_id)
        finally:
            self._operation_lock.release()

    def fn_disconnect(self):
        if not self._operation_lock.acquire(blocking=False):
            raise CANConnectionError("A CAN operation is already running.")
        try:
            state = self.snapshot.state
            if state == State.DISCONNECTED:
                return
            if state == State.ERROR:
                self._transition(State.DISCONNECTED, rediscovery_required=self.snapshot.rediscovery_required)
                return
            if state != State.CONNECTED:
                raise CANConnectionError("CAN resource cleanup is uncertain. Restart V-CODE before reconnecting.", recovery_required=True)
            config = self.snapshot.config
            self._transition(State.DISCONNECTING, config=config)
            try:
                self._backend.fn_close()
            except Exception as error:
                LOG.exception("CAN service disconnect failed")
                failure = CANConnectionError("Cannot confirm Vector CAN cleanup. Restart V-CODE before reconnecting.", recovery_required=True)
                self._transition(State.RECOVERY_REQUIRED, config=config, error=str(failure))
                raise failure from error
            self._transition(State.DISCONNECTED)
        finally:
            self._operation_lock.release()

    def fn_is_connected(self):
        return self.snapshot.state == State.CONNECTED

    @property
    def capture_session_id(self):
        return getattr(self._backend,'capture_session_id','') if self.fn_is_connected() else ''

    @property
    def trusted_bench(self):
        with self._state_lock:
            grant = self._trusted_bench
            context = self._bench_context
            return grant if (grant and context and context.authorized and grant.context_id == context.context_id
                and self.fn_is_connected() and grant.connection_id == self.capture_session_id) else None

    def fn_configure_bench_context(self, context):
        """A changed context revokes immediately; only an explicitly configured Connect issues a grant."""
        if context is not None and not isinstance(context,BenchAuthorizationContext):
            raise DiagnosticValidationError('Invalid bench authorization context.')
        with self._bench_tx_lock, self._state_lock:
            if context != self._bench_context:
                self._security_authority.revoke_all()
                self._bench_revision += 1
                self._trusted_bench = None
                self._bench_context = context

    def fn_revoke_trusted_bench(self):
        with self._bench_tx_lock, self._state_lock:
            self._security_authority.revoke_all()
            self._bench_revision += 1
            self._trusted_bench = None

    def _validate_bench_authorization(self, request):
        if not request.bench_authorization_id: return
        with self._state_lock:
            grant = self.trusted_bench
            if (grant is None or grant.authorization_id != request.bench_authorization_id
                    or not grant.permits(request,self.capture_session_id)):
                raise DiagnosticValidationError('Connection bench authorization expired or does not cover this request.')

    def fn_confirm_trusted_request(self, request):
        with self._state_lock:
            grant = self.trusted_bench
            if grant is None or not grant.permits(request,self.capture_session_id): return None
            return replace(request, confirmed=True, bench_authorization_id=grant.authorization_id)

    def fn_begin_diagnostic(self, request):
        validate_send_policy(request)
        if not self._operation_lock.acquire(blocking=False):
            raise CANConnectionError('A CAN operation is already running.')
        try:
            with self._state_lock:
                if self.snapshot.state != State.CONNECTED:
                    raise CANConnectionError('Connect the selected Vector channel before sending.')
                self._validate_bench_authorization(request)
                if self._auto_context is not None:
                    flow = self._auto_context[0]
                    self._check_auto_security(flow)
                    if not self.is_auto_request(request):
                        raise DiagnosticValidationError('The CAN owner is reserved by Auto SecurityAccess.')
                    if request is flow.seed_request:
                        if self._auto_seed_admitted:
                            raise DiagnosticValidationError('Auto seed request cannot be replayed.')
                        self._auto_seed_admitted = True
                from core.security_submission import is_key_submission
                if is_key_submission(request): self._validate_key_submission(request,claim=True)
                if request.uds_payload[:1] in (b'\x10', b'\x11'):
                    self._security_epoch+=1
                    self._uds_session=None
                    self._uds_session_target=None
                    self._security_authority.revoke_all()
                self._diagnostic_request=request
                self._diagnostic_owner=get_ident()
        except Exception:
            self._operation_lock.release()
            raise

    def _guard_diagnostic_owner(self, *, check_auto=True):
        if self._diagnostic_request is None or self._diagnostic_owner != get_ident() or self.snapshot.state != State.CONNECTED:
            raise CANConnectionError('Diagnostic I/O requires the active transaction owner.')
        if check_auto and self._auto_context is not None:
            try:
                self._check_auto_security(self._auto_context[0])
            except DiagnosticValidationError:
                raise DiagnosticCancelled('Auto L1 workflow context revoked.') from None

    def fn_send_diagnostic_frame(self, can_id, data):
        self._guard_diagnostic_owner()
        if can_id != self._diagnostic_request.tx_id or not isinstance(data,bytes) or not 1 <= len(data) <= 8:
            raise CANConnectionError('Invalid diagnostic transport frame/target.')
        from core.security_submission import is_key_submission
        if is_key_submission(self._diagnostic_request):
            with self._bench_tx_lock:
                try: self._validate_key_submission(self._diagnostic_request)
                except DiagnosticValidationError as error: raise DiagnosticCancelled(str(error)) from None
                return self._backend.fn_send_frame(can_id,data)
        if not self._diagnostic_request.bench_authorization_id:
            return self._backend.fn_send_frame(can_id,data)
        with self._bench_tx_lock:
            try:
                self._validate_bench_authorization(self._diagnostic_request)
            except DiagnosticValidationError as error:
                # Use cooperative cancellation, not a native capture/BLF fault.
                raise DiagnosticCancelled(str(error)) from error
            return self._backend.fn_send_frame(can_id,data)

    def fn_receive_diagnostic_frame(self):
        self._guard_diagnostic_owner()
        from core.security_submission import is_key_submission
        if is_key_submission(self._diagnostic_request):
            with self._bench_tx_lock:
                try: self._validate_key_submission(self._diagnostic_request)
                except DiagnosticValidationError as error: raise DiagnosticCancelled(str(error)) from None
        return self.fn_receive_capture_frame()

    def fn_receive_capture_frame(self):
        """Nonblocking read on the native owner; idle capture holds no lease."""
        if self.snapshot.state != State.CONNECTED:
            raise CANConnectionError('Capture requires a connected CAN bus.')
        return self._backend.fn_receive_frame()

    def fn_end_diagnostic(self, transaction_id):
        # Revoked authorization must stop I/O, never prevent owner cleanup.
        self._guard_diagnostic_owner(check_auto=False)
        if self._diagnostic_request.transaction_id != transaction_id:
            raise CANConnectionError('Stale diagnostic transaction.')
        self._security_authority.retire(self._diagnostic_request)
        self._diagnostic_request=None
        self._diagnostic_owner=None
        self._operation_lock.release()

    def fn_transport_failed(self, error):
        """Owner calls after ending the lease; never used for ordinary silence."""
        self.fn_disconnect()
        self._transition(State.DISCONNECTED,error=str(error),rediscovery_required=True)

    def fn_refresh(self) -> tuple[CANDeviceInfo, ...]:
        if not self._operation_lock.acquire(blocking=False):
            raise CANDiscoveryError("A CAN operation is already running.")
        try:
            if self.snapshot.state not in (State.DISCONNECTED, State.ERROR):
                raise CANDiscoveryError("Disconnect the active CAN session before refreshing Vector devices.")
            try:
                devices = self._refresh_devices()
            except Exception:
                if getattr(self._backend, "recovery_required", False) is True:
                    self._transition(State.RECOVERY_REQUIRED, error="Cannot confirm Vector driver cleanup. Restart V-CODE.")
                raise
            if self.snapshot.state == State.ERROR or self.snapshot.rediscovery_required:
                self._transition(State.DISCONNECTED)
            return devices
        finally:
            self._operation_lock.release()

    def _refresh_devices(self):
        if self._backend.fn_is_connected():
            raise CANDiscoveryError("Disconnect the active CAN session before refreshing Vector devices.")
        refresh = getattr(self._backend, "fn_refresh", None)
        devices = refresh() if callable(refresh) else ()
        if not isinstance(devices, (tuple, list)):
            raise CANDiscoveryError("Invalid Vector discovery result.")
        identities, global_indices = set(), set()
        for device in devices:
            if not isinstance(device, CANDeviceInfo) or not isinstance(device.channels, tuple):
                raise CANDiscoveryError("Invalid Vector device metadata.")
            if not isinstance(device.name, str) or not device.name.strip() or not isinstance(device.discovery_id, str):
                raise CANDiscoveryError("Invalid Vector device name.")
            for value in (device.serial, device.hw_type, device.hw_index):
                if value is not None and (isinstance(value, bool) or not isinstance(value, Integral) or value < 0):
                    raise CANDiscoveryError("Invalid Vector hardware identity.")
            if device.identity in identities:
                raise CANDiscoveryError("Ambiguous Vector device identity.")
            identities.add(device.identity)
            for channel in device.channels:
                if not isinstance(channel, CANChannelInfo) or not isinstance(channel.supports_fd, bool):
                    raise CANDiscoveryError("Invalid Vector channel metadata.")
                if not isinstance(channel.name, str) or not channel.name.strip():
                    raise CANDiscoveryError("Invalid Vector channel name.")
                for value in (channel.channel, channel.channel_index, channel.hw_channel):
                    if value is not None and (isinstance(value, bool) or not isinstance(value, Integral) or value < 0):
                        raise CANDiscoveryError("Invalid Vector channel index.")
                if channel.channel is None:
                    raise CANDiscoveryError("Vector channel is not identified.")
                if channel.channel_index is not None:
                    if channel.channel_index in global_indices:
                        raise CANDiscoveryError("Ambiguous Vector global channel index.")
                    global_indices.add(channel.channel_index)
        return tuple(devices)

    @staticmethod
    def _validate_config(config: CANConfig):
        if not isinstance(config, CANConfig):
            raise CANValidationError("Invalid CAN configuration.")
        if config.bench_context is not None and not isinstance(config.bench_context,BenchAuthorizationContext):
            raise CANValidationError('Invalid connection bench authorization context.')

        if not isinstance(config.interface, str) or config.interface != "vector":
            raise CANValidationError("Only Vector CAN interface is supported.")

        if isinstance(config.channel, bool) or not isinstance(config.channel, Integral) or config.channel < 0:
            raise CANValidationError("CAN channel index must be 0 or greater.")

        for value in (config.serial, config.channel_index, config.hw_type, config.hw_index, config.hw_channel):
            if value is not None and (isinstance(value, bool) or not isinstance(value, Integral) or value < 0):
                raise CANValidationError("Invalid Vector connection metadata.")

        if config.channel_index is not None and config.serial is None and (config.hw_type is None or config.hw_index is None):
            raise CANValidationError("The selected channel has no reliable hardware identity. Refresh Vector devices.")
        if config.channel_index is None and any(value is not None for value in (config.serial, config.hw_type, config.hw_index, config.hw_channel)):
            raise CANValidationError("A discovered Vector target requires an explicit global channel index.")
        if config.fd:
            raise CANValidationError("CAN FD connections are not supported in this milestone.")

        if isinstance(config.bitrate, bool) or not isinstance(config.bitrate, Integral) or config.bitrate not in SUPPORTED_BITRATES:
            raise CANValidationError(
                "Unsupported bitrate. Use 125000, 250000, 500000, or 1000000."
            )
