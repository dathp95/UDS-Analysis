from __future__ import annotations

from services.can.can_config import CANConfig
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
        self._backend = backend or VectorBackend()

    def fn_connect(self, config: CANConfig):
        self._validate_config(config)
        self._backend.fn_open(config)

    def fn_disconnect(self):
        self._backend.fn_close()

    def fn_is_connected(self):
        return self._backend.fn_is_connected()

    def fn_refresh(self):
        refresh = getattr(self._backend, "fn_refresh", None)
        if callable(refresh):
            return refresh()
        return None

    @staticmethod
    def _validate_config(config: CANConfig):
        if not isinstance(config, CANConfig):
            raise CANValidationError("Invalid CAN configuration.")

        if config.interface.strip().lower() != "vector":
            raise CANValidationError("Only Vector CAN interface is supported.")

        if config.channel < 0:
            raise CANValidationError("CAN channel index must be 0 or greater.")

        if config.bitrate not in SUPPORTED_BITRATES:
            raise CANValidationError(
                "Unsupported bitrate. Use 125000, 250000, 500000, or 1000000."
            )
