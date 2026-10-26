"""Immutable Classical CAN acquisition record; no driver or widget ownership."""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class CanFrameView:
    timestamp_s: float
    direction: str
    can_id: int
    dlc: int
    data: bytes
    wall_timestamp_s: float | None = None
    monotonic_timestamp_s: float | None = None
    channel: int | str | None = None
    is_extended_id: bool = False
    tx_origin: str = ''
    is_remote_frame: bool = False
    is_error_frame: bool = False
    session_id: str = ''
    sequence: int = 0
    source_channel: int | str | None = None
    source_timestamp_s: float | None = None
    timestamp_source: str = ''
    echo_of_sequence: int | None = None

    def __post_init__(self):
        for value in (self.wall_timestamp_s,self.monotonic_timestamp_s):
            if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float)) or not isfinite(value)):
                raise ValueError('Invalid raw frame timestamp.')
        if (isinstance(self.timestamp_s, bool) or not isinstance(self.timestamp_s, (int, float))
                or not isfinite(self.timestamp_s) or self.timestamp_s < 0):
            raise ValueError("Frame timestamp must be finite and nonnegative.")
        if self.direction not in ("TX", "RX"):
            raise ValueError("Frame direction must be TX or RX.")
        if isinstance(self.can_id, bool) or not isinstance(self.can_id, int) or not 0 <= self.can_id <= 0x1FFFFFFF:
            raise ValueError("Invalid CAN identifier.")
        if (isinstance(self.dlc, bool) or not isinstance(self.dlc, int) or not 0 <= self.dlc <= 8
                or not isinstance(self.data, bytes) or len(self.data) > self.dlc):
            raise ValueError("Expected classic CAN frame display data.")
