"""Memory-only ECU peer for explicit tests/simulation. No device/Vector delegate.

Not a discovery option. The real owner and ISO-TP stack talk to this in-memory
peer exactly as to a driver. PUBLIC dummy HMAC material must never authorize I/O.
"""
from collections import deque
import hmac
from threading import get_ident
import time
from uuid import uuid4

from core.can_interface_view import CanFrameView
from services.can.hmac_sha1_provider import hmac_sha1_key


class SimulatedCANBackend:
    def __init__(self,*,tx_id=0x681,rx_id=0x601):
        self.tx_id,self.rx_id=tx_id,rx_id
        self.seed=bytes(range(16))
        self.key_response=b'\x67\x02'
        self.pending_delay=0
        self.response_can_id=None
        self.frames=[]
        self.requests=[]
        self.threads=[]
        self._connected=False
        self.capture_session_id=''
        self._rx=deque()
        self._deferred=deque()
        self._outgoing=b''
        self._incoming=bytearray()
        self._incoming_size=0
        self._extended=False

    def fn_open(self,config):
        self._owner=get_ident()
        self.threads.append(self._owner)
        self._origin=time.monotonic()
        self._channel=config.channel
        self._connected=True
        self._extended=False
        self._rx.clear();self._deferred.clear()
        self.capture_session_id=uuid4().hex

    def fn_is_connected(self): return self._connected

    def _guard(self):
        if not self._connected or get_ident()!=self._owner:
            raise RuntimeError('Simulator I/O requires its connected owner thread.')
        self.threads.append(get_ident())

    def fn_close(self):
        self._guard()
        self._connected=False
        self.capture_session_id=''
        self._rx.clear();self._deferred.clear()

    def _frame(self,direction,data,can_id):
        now=time.monotonic()
        frame=CanFrameView(now-self._origin,direction,can_id,len(data),bytes(data),time.time(),now,
                           self._channel,session_id=self.capture_session_id,sequence=len(self.frames)+1,
                           timestamp_source='simulated',tx_origin='simulator_accepted' if direction=='TX' else '')
        self.frames.append(frame)
        return frame

    def _enqueue(self,data):
        self._rx.append(self._frame('RX',data,self.response_can_id or self.rx_id))

    def _response(self,payload):
        if payload is None: return
        if len(payload)<=7:
            self._enqueue(bytes((len(payload),))+payload+bytes(7-len(payload)))
        else:
            self._enqueue(bytes((0x10|len(payload)>>8,len(payload)&255))+payload[:6])
            self._outgoing=payload[6:]

    def _uds(self,payload):
        self.requests.append(payload)
        if payload in (b'\x10\x01',b'\x10\x03'):
            self._extended=payload[1]==3
            self._response(b'\x50'+payload[1:2])
        elif payload==b'\x27\x01':
            self._response(b'\x67\x01'+self.seed if self._extended else b'\x7f\x27\x7f')
        elif payload[:2]==b'\x27\x02':
            if not self._extended:
                self._response(b'\x7f\x27\x7f')
            elif not hmac.compare_digest(payload[2:],hmac_sha1_key(self.seed,b'SIMUL8!!')):
                self._response(b'\x7f\x27\x35')
            elif self.pending_delay:
                self._response(b'\x7f\x27\x78')
                self._deferred.append((time.monotonic()+self.pending_delay,self.key_response))
            else:
                self._response(self.key_response)
        else:
            self._response(bytes((0x7f,payload[0],0x11)))

    def fn_send_frame(self,can_id,data):
        self._guard()
        frame=self._frame('TX',data,can_id)
        if can_id!=self.tx_id: return frame
        kind=data[0]>>4
        if kind==0:
            self._uds(data[1:1+(data[0]&15)])
        elif kind==1:
            self._incoming_size=((data[0]&15)<<8)|data[1]
            self._incoming=bytearray(data[2:])
            self._next_sequence=1
            self._enqueue(b'\x30'+bytes(7))
        elif kind==2 and self._incoming_size:
            if data[0]&15!=self._next_sequence: raise ValueError('Simulator received an invalid CF sequence.')
            self._next_sequence=(self._next_sequence+1)&15
            self._incoming.extend(data[1:])
            if len(self._incoming)>=self._incoming_size:
                payload=bytes(self._incoming[:self._incoming_size])
                self._incoming_size=0
                self._uds(payload)
        elif kind==3 and self._outgoing:
            for index,offset in enumerate(range(0,len(self._outgoing),7),1):
                block=self._outgoing[offset:offset+7]
                self._enqueue(bytes((0x20|(index&15),))+block+bytes(7-len(block)))
            self._outgoing=b''
        return frame

    def fn_receive_frame(self):
        self._guard()
        while self._deferred and self._deferred[0][0]<=time.monotonic():
            self._response(self._deferred.popleft()[1])
        return self._rx.popleft() if self._rx else None
