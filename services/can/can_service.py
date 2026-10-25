from __future__ import annotations

from numbers import Integral

from services.can.can_config import CANConfig
from services.can.can_device import CANChannelInfo, CANDeviceInfo, CANDiscoveryError
from services.can.vector_backend import VectorBackend


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

    def fn_connect(self, config: CANConfig):
        self._validate_config(config)
        self._backend.fn_open(config)

    def fn_disconnect(self):
        self._backend.fn_close()

    def fn_is_connected(self):
        return self._backend.fn_is_connected()

    def fn_refresh(self) -> tuple[CANDeviceInfo, ...]:
        if self.fn_is_connected():
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

        if config.interface.strip().lower() != "vector":
            raise CANValidationError("Only Vector CAN interface is supported.")

        if isinstance(config.channel, bool) or not isinstance(config.channel, Integral) or config.channel < 0:
            raise CANValidationError("CAN channel index must be 0 or greater.")

        for value in (config.serial, config.channel_index):
            if value is not None and (isinstance(value, bool) or not isinstance(value, Integral) or value < 0):
                raise CANValidationError("Invalid Vector connection metadata.")

        if config.bitrate not in SUPPORTED_BITRATES:
            raise CANValidationError(
                "Unsupported bitrate. Use 125000, 250000, 500000, or 1000000."
            )
