from __future__ import annotations

from collections.abc import Mapping
from importlib import import_module
import logging
from numbers import Integral

from services.can.can_config import CANConfig
from services.can.can_device import (
    CANChannelInfo, CANDeviceInfo, CANDependencyError, CANDiscoveryError,
    CANNoChannelsError, VectorDriverUnavailableError,
)

LOG = logging.getLogger(__name__)


class CANConnectionError(RuntimeError):
    pass


class VectorBackend:

    def __init__(self, *, can_module=None, vector_module=None):
        self._bus = None
        self._can_module = can_module
        self._vector_module = vector_module

    def fn_open(self, config: CANConfig):
        if self._bus is not None:
            self.fn_close()

        try:
            can = self._can_module or import_module("can")
        except ImportError as error:
            raise CANConnectionError(
                "python-can is not installed. Please install python-can before connecting Vector hardware."
            ) from error

        try:
            metadata = {}
            if config.serial is not None:
                metadata["serial"] = config.serial
            if config.channel_index is not None:
                metadata["channel_index"] = config.channel_index
            self._bus = can.Bus(
                interface=config.interface,
                channel=config.channel,
                bitrate=config.bitrate,
                app_name="",
                **metadata,
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

    def fn_refresh(self) -> tuple[CANDeviceInfo, ...]:
        if self.fn_is_connected():
            raise CANDiscoveryError("Disconnect the active CAN session before refreshing Vector devices.")
        try:
            can = self._can_module or import_module("can")
        except ImportError as error:
            raise CANDependencyError("python-can is not installed.") from error
        try:
            vector = self._vector_module or import_module("can.interfaces.vector.canlib")
        except (ImportError, OSError) as error:
            raise VectorDriverUnavailableError("Vector XL Driver is unavailable.") from error
        if vector.xldriver is None:
            raise VectorDriverUnavailableError("Vector XL Driver is unavailable.")

        # python-can 4.6.1 get_channel_configs() suppresses VectorError. A strict
        # driver query distinguishes a driver failure from a valid empty result.
        # Reuse its existing XL bindings, never xlOpenPort or can.Bus here.
        # Source: https://python-can.readthedocs.io/en/stable/_modules/can/interfaces/vector/canlib.html
        driver = vector.xldriver
        try:
            driver.xlOpenDriver()
            try:
                snapshot = vector.xlclass.XLdriverConfig()
                driver.xlGetDriverConfig(snapshot)
                can_mask = int(vector.xldefine.XL_BusCapabilities.XL_BUS_ACTIVE_CAP_CAN)
                total = snapshot.channelCount
                can_count = sum(bool(snapshot.channel[i].channelBusCapabilities & can_mask) for i in range(total))
            finally:
                driver.xlCloseDriver()
        except Exception as error:
            LOG.exception("Vector driver configuration query failed")
            raise VectorDriverUnavailableError("Vector XL Driver is unavailable.") from error
        if not total:
            return ()
        if not can_count:
            raise CANNoChannelsError("The detected Vector device has no available CAN channel.")
        try:
            # None is forwarded to concurrent.futures.wait in installed 4.6.1:
            # keep ownership until detection stops, rather than orphaning timed-out calls.
            records = can.detect_available_configs(interfaces=["vector"], timeout=None)
            if not records:
                raise CANDiscoveryError("Vector discovery returned no configuration for reported CAN hardware. Refresh again.")
            return self._normalize_devices(records, can_mask)
        except CANDiscoveryError:
            raise
        except Exception as error:
            LOG.exception("Unexpected Vector discovery failure")
            raise CANDiscoveryError("Vector device discovery failed. Check the application log.") from error

    @staticmethod
    def _normalize_devices(records, can_mask):
        groups = {}
        global_indices = set()
        for ordinal, record in enumerate(records):
            if not isinstance(record, Mapping):
                raise CANDiscoveryError("Invalid Vector discovery metadata.")
            if record.get("interface", "vector") != "vector":
                continue
            native = record.get("vector_channel_config")
            capabilities = getattr(native, "channel_bus_capabilities", None)
            if capabilities is not None and not int(capabilities) & can_mask:
                continue

            def number(key, attribute=None):
                value = record.get(key)
                if value is None and native is not None:
                    value = getattr(native, attribute or key, None)
                if value is None:
                    return None
                if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
                    raise CANDiscoveryError(f"Invalid Vector {key} metadata.")
                return int(value)

            serial = number("serial", "serial_number")
            hw_type, hw_index = number("hw_type"), number("hw_index")
            hw_channel, channel_index = number("hw_channel"), number("channel_index")
            channel = number("channel")
            if channel is None:
                channel = hw_channel if hw_channel is not None else channel_index
            if channel is None:
                raise CANDiscoveryError("Vector discovery did not identify a CAN channel.")
            if channel_index is not None:
                if channel_index in global_indices:
                    raise CANDiscoveryError("Ambiguous duplicate Vector global channel index.")
                global_indices.add(channel_index)
            name = record.get("name") or getattr(native, "name", None)
            name = name.strip() if isinstance(name, str) and name.strip() else "Vector Device"
            if hw_type is not None and hw_index is not None:
                key = ("hardware", serial, hw_type, hw_index)
            else:
                key = ("isolated", channel_index if channel_index is not None else ordinal)
            fd = record.get("supports_fd", False)
            if fd is not None and not isinstance(fd, (bool, Integral)):
                raise CANDiscoveryError("Invalid Vector CAN FD capability metadata.")
            label = f"CAN {hw_channel + 1}" if hw_channel is not None else f"CAN {channel + 1}"
            info = CANChannelInfo(channel, channel_index, label, bool(fd), hw_channel)
            if key not in groups:
                groups[key] = (name, serial, hw_type, hw_index, [])
            groups[key][4].append(info)
        if not groups:
            raise CANNoChannelsError("The detected Vector device has no available CAN channel.")
        return tuple(CANDeviceInfo(name, serial, hw_type, hw_index, tuple(channels), repr(key))
                     for key, (name, serial, hw_type, hw_index, channels) in groups.items())

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
