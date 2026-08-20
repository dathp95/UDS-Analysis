from __future__ import annotations

from services.can.can_config import CANConfig


class CANConnectionError(RuntimeError):
    pass


class VectorBackend:

    def __init__(self):
        self._bus = None

    def fn_open(self, config: CANConfig):
        if self._bus is not None:
            self.fn_close()

        try:
            import can
        except ImportError as error:
            raise CANConnectionError(
                "python-can is not installed. Please install python-can before connecting Vector hardware."
            ) from error

        try:
            self._bus = can.Bus(
                interface=config.interface,
                channel=config.channel,
                bitrate=config.bitrate,
                app_name="",
            )
        except Exception as error:
            self._bus = None
            raise CANConnectionError(
                self._translate_error(error)
            ) from error

    def fn_close(self):
        bus = self._bus
        self._bus = None
        if bus is None:
            return

        try:
            shutdown = getattr(bus, "shutdown", None)
            if callable(shutdown):
                shutdown()
                return

            close = getattr(bus, "close", None)
            if callable(close):
                close()
        except Exception as error:
            raise CANConnectionError(
                f"Cannot release Vector CAN resource: {error}"
            ) from error

    def fn_is_connected(self):
        return self._bus is not None

    def fn_refresh(self):
        return None

    @staticmethod
    def _translate_error(error: Exception):
        message = str(error).strip() or error.__class__.__name__
        lower_message = message.lower()

        if "xl driver library" in lower_message or "xl_driver" in lower_message:
            return "XL Driver Library is unavailable. Please check Vector driver installation."

        if "driver" in lower_message and "not" in lower_message:
            return "Vector driver is missing or unavailable."

        if "channel" in lower_message and "invalid" in lower_message:
            return "Invalid Vector CAN channel. Please select another channel."

        if "hardware" in lower_message or "device" in lower_message:
            return "Vector hardware is not connected or not detected."

        if "in use" in lower_message or "already" in lower_message:
            return "Selected Vector CAN channel is already in use."

        if "bitrate" in lower_message or "baud" in lower_message:
            return "Cannot configure the requested CAN bitrate."

        return f"Cannot connect to Vector CAN interface: {message}"
