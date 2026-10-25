from __future__ import annotations

from numbers import Integral
from threading import Lock, RLock
import logging

from services.can.can_config import CANConfig
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
        self._snapshot = CANConnectionSnapshot()

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

    def fn_connect(self, config: CANConfig):
        self._validate_config(config)
        if not self._operation_lock.acquire(blocking=False):
            raise CANConnectionError("A CAN operation is already running.")
        try:
            if self.snapshot.state not in (State.DISCONNECTED, State.ERROR):
                raise CANConnectionError("Disconnect cleanly before opening another CAN connection.")
            if self.snapshot.rediscovery_required:
                raise CANConnectionError("Refresh Vector devices before connecting again.", rediscovery_required=True)
            self._transition(State.CONNECTING, config=config)
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
            self._transition(State.CONNECTED, config=config)
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
