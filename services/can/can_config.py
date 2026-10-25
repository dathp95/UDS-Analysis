from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CANConfig:
    interface: str
    channel: int
    bitrate: int
    fd: bool = False
    serial: int | None = None
    channel_index: int | None = None
    hw_type: int | None = None
    hw_index: int | None = None
    hw_channel: int | None = None
