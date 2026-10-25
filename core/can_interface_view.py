"""Future monitor input is presentation data, not a bus or transport API."""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class CanFrameView:
    timestamp_s: float
    direction: str
    can_id: int
    dlc: int
    data: bytes

    def __post_init__(self):
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
