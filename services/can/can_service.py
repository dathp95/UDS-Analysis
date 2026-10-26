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
                self._bench_revision += 1
                self._trusted_bench = None
                self._bench_context = context

    def fn_revoke_trusted_bench(self):
        with self._bench_tx_lock, self._state_lock:
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
                self._diagnostic_request=request
                self._diagnostic_owner=get_ident()
        except Exception:
            self._operation_lock.release()
            raise

    def _guard_diagnostic_owner(self):
        if self._diagnostic_request is None or self._diagnostic_owner != get_ident() or self.snapshot.state != State.CONNECTED:
            raise CANConnectionError('Diagnostic I/O requires the active transaction owner.')

    def fn_send_diagnostic_frame(self, can_id, data):
        self._guard_diagnostic_owner()
        if can_id != self._diagnostic_request.tx_id or not isinstance(data,bytes) or not 1 <= len(data) <= 8:
            raise CANConnectionError('Invalid diagnostic transport frame/target.')
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
        return self.fn_receive_capture_frame()

    def fn_receive_capture_frame(self):
        """Nonblocking read on the native owner; idle capture holds no lease."""
        if self.snapshot.state != State.CONNECTED:
            raise CANConnectionError('Capture requires a connected CAN bus.')
        return self._backend.fn_receive_frame()

    def fn_end_diagnostic(self, transaction_id):
        self._guard_diagnostic_owner()
        if self._diagnostic_request.transaction_id != transaction_id:
            raise CANConnectionError('Stale diagnostic transaction.')
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
