"""Narrow lifecycle adapter for python-can 4.6.1 (no new XL bindings).

VectorBus.shutdown suppresses VectorError around all three cleanup calls, so a
failed deactivate can skip port/driver close. Track only this bus's acquisitions
and confirm each release independently. Never patch module-global driver state.
Source: https://python-can.readthedocs.io/en/stable/_modules/can/interfaces/vector/canlib.html
"""

import logging

LOG = logging.getLogger(__name__)


class _OwnedDriver:
    def __init__(self, driver, invalid_port):
        self.driver = driver
        self.invalid_port = invalid_port
        self.driver_open = False
        self.port = None
        self.activation = None
        self.failed = False

    def __getattr__(self, name):
        return getattr(self.driver, name)

    def xlOpenDriver(self):
        result = self.driver.xlOpenDriver()
        self.driver_open = True
        return result

    def xlOpenPort(self, handle, *args):
        try:
            return self.driver.xlOpenPort(handle, *args)
        finally:
            if handle.value != self.invalid_port:
                self.port = handle

    def xlActivateChannel(self, port, mask, *args):
        self.activation = (port, mask)
        return self.driver.xlActivateChannel(port, mask, *args)

    def release(self):
        if self.failed:
            raise RuntimeError("Previous Vector resource cleanup failed; restart required")
        # A failed deactivate does not prevent attempting close-port. A confirmed
        # port close also releases its channel activation, so no stale handle is retried.
        if self.activation is not None:
            try:
                self.driver.xlDeactivateChannel(*self.activation)
            except Exception:
                LOG.warning("Vector channel deactivation failed; attempting port close", exc_info=True)
        try:
            if self.port is not None:
                self.driver.xlClosePort(self.port)
                self.port = None
                self.activation = None
            if self.driver_open:
                self.driver.xlCloseDriver()
                self.driver_open = False
        except Exception:
            self.failed = True
            raise


def new_owned_vector_bus(vector):
    """Allocate before initialization so the caller can clean a partial open."""
    class OwnedVectorBus(vector.VectorBus):
        @property
        def xldriver(self):
            return self._owned_driver

        @xldriver.setter
        def xldriver(self, driver):
            self._owned_driver = _OwnedDriver(driver, vector.xldefine.XL_INVALID_PORTHANDLE)

        def shutdown(self):
            if hasattr(self, "_owned_driver"):
                self._owned_driver.release()
            # BusABC cleanup (periodic task bookkeeping) without VectorBus's
            # suppressed native cleanup. M02 creates no periodic tasks.
            super(vector.VectorBus, self).shutdown()

        def __del__(self):
            # Native resources belong to the executor, never to GC on an arbitrary
            # thread. Backend retains uncertain owners; no retry from a finalizer.
            pass

    bus = OwnedVectorBus.__new__(OwnedVectorBus)
    bus._is_shutdown = True
    return bus
