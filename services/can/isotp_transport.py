"""Cooperative can-isotp 2.0.7 adapter. Never starts library RX/TX threads.

Source: https://can-isotp.readthedocs.io/en/latest/isotp/implementation.html
"""
from collections import deque
from threading import Event

import isotp

from core.diagnostic_request import validate_send_policy,response_belongs_to_request,DiagnosticCancelled


class IsoTpTransport:
    def __init__(self, request, send_frame, cancelled=None):
        validate_send_policy(request)
        self.request=request
        self.cancelled=cancelled if cancelled is not None else Event()
        self._inbox=deque()
        self.error=None
        settings=request.settings

        def transmit(message):
            if self.cancelled.is_set(): raise DiagnosticCancelled()
            send_frame(message.arbitration_id,bytes(message.data))

        self.layer=isotp.TransportLayerLogic(
            rxfn=lambda timeout: self._inbox.popleft() if self._inbox else None,
            txfn=transmit,
            address=isotp.Address(isotp.AddressingMode.Normal_11bits,txid=request.tx_id,rxid=request.rx_id),
            error_handler=self._error,
            params=dict(stmin=settings.stmin,blocksize=settings.block_size,wftmax=3,
                        rx_flowcontrol_timeout=max(1,int(settings.fc_timeout_s*1000)),
                        rx_consecutive_frame_timeout=max(1,int(settings.cf_timeout_s*1000)),
                        tx_data_length=8,tx_padding=settings.padding,
                        tx_data_min_length=8 if settings.padding is not None else None,
                        max_frame_size=settings.max_payload,blocking_send=False,
                        rate_limit_enable=True,rate_limit_max_bitrate=32000,rate_limit_window_size=0.02))
        self.layer.send(request.uds_payload)

    def _error(self, error):
        if self.error is None: self.error=error

    def feed(self, frame):
        if (frame.direction != 'RX' or frame.can_id != self.request.rx_id or frame.is_extended_id
                or frame.is_remote_frame or frame.is_error_frame):
            return
        data=frame.data
        if not data or frame.dlc != len(data):
            self._error(ValueError('Malformed CAN DLC/data length.'))
            return
        kind=data[0] >> 4
        if kind == 0 and (data[0]&0x0F == 0 or data[0]&0x0F > len(data)-1):
            self._error(ValueError('Malformed ISO-TP Single Frame length.'))
            return
        # Do not let the library generate FC for a different service/unsolicited FF.
        if kind in (0,1):
            if self.layer.transmitting(): return
            offset=1 if kind == 0 else 2
            if len(data) > offset:
                prefix=data[offset:offset+(data[0]&0x0F)] if kind == 0 else data[offset:]
                if not response_belongs_to_request(self.request,prefix): return
        if kind == 2 and not self.layer.is_rx_active(): return
        if kind == 3 and not self.layer.transmitting(): return
        if len(self._inbox) >= 64:
            self._error(ValueError('ISO-TP ingress budget exceeded.'))
            return
        self._inbox.append(isotp.CanMessage(arbitration_id=frame.can_id,dlc=frame.dlc,data=data,extended_id=False))

    def process(self):
        if self.cancelled.is_set(): raise DiagnosticCancelled()
        self.layer.process(rx_timeout=0.0)

    def receive(self):
        payload=self.layer.recv()
        return bytes(payload) if payload is not None else None

    @property
    def transmitting(self): return self.layer.transmitting()

    @property
    def receiving(self): return self.layer.is_rx_active()

    @property
    def timed_out(self):
        return isinstance(self.error,(isotp.FlowControlTimeoutError,isotp.ConsecutiveFrameTimeoutError))

    def stop(self):
        self.layer.reset()
        self._inbox.clear()
