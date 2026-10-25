from dataclasses import dataclass
from enum import Enum

from services.can.can_config import CANConfig


class CANConnectionState(Enum):
    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"
    DISCONNECTING = "Disconnecting"
    ERROR = "Error"
    RECOVERY_REQUIRED = "Recovery required"


class CANConnectionError(RuntimeError):
    def __init__(self, message, *, recovery_required=False, rediscovery_required=False):
        super().__init__(message)
        self.recovery_required = recovery_required
        self.rediscovery_required = rediscovery_required


@dataclass(frozen=True)
class CANConnectionSnapshot:
    state: CANConnectionState = CANConnectionState.DISCONNECTED
    config: CANConfig | None = None
    error: str = ""
    rediscovery_required: bool = False
