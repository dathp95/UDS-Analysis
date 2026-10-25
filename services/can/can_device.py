from dataclasses import dataclass


class CANDiscoveryError(RuntimeError):
    pass


class CANDependencyError(CANDiscoveryError):
    pass


class VectorDriverUnavailableError(CANDiscoveryError):
    pass


class CANNoChannelsError(CANDiscoveryError):
    pass


@dataclass(frozen=True)
class CANChannelInfo:
    channel: int
    channel_index: int | None
    name: str
    supports_fd: bool
    hw_channel: int | None = None

    @property
    def can_connect(self) -> bool:
        # The installed Vector backend accepts an explicit global index.
        return self.channel_index is not None

    @property
    def identity(self):
        return self.hw_channel if self.hw_channel is not None else self.channel


@dataclass(frozen=True)
class CANDeviceInfo:
    name: str
    serial: int | None
    hw_type: int | None
    hw_index: int | None
    channels: tuple[CANChannelInfo, ...]
    discovery_id: str = ""

    @property
    def identity(self):
        if self.hw_type is not None and self.hw_index is not None:
            return ("hardware", self.serial, self.hw_type, self.hw_index)
        return ("isolated", self.discovery_id or tuple(c.channel_index for c in self.channels))
