"""One manual UDS transaction; protocol and expectation are separate concerns."""
from collections import deque
from threading import Event
import time

from core.diagnostic_request import DiagnosticResult,DiagnosticOutcome as Outcome,response_belongs_to_request
from services.can.isotp_transport import IsoTpTransport,DiagnosticCancelled


class DiagnosticClient:
    def __init__(self, request, send_frame, cancelled=None, clock=time.monotonic):
        self.request=request
        self.clock=clock
        self.started=clock()
        self.cancelled=cancelled if cancelled is not None else Event()
        self.engine=IsoTpTransport(request,send_frame,self.cancelled)
        self.result=None
        self.deadline=None
        self.pending_times=deque(maxlen=256)
        self.pending_count=0

    def feed(self, frame):
        if self.result is None: self.engine.feed(frame)

    def poll(self):
        if self.result is not None: return self.result
        now=self.clock()
        if self.cancelled.is_set(): return self.cancel()
        if now-self.started >= self.request.settings.total_s:
            return self.finish(Outcome.TIMEOUT,detail='Maximum diagnostic transaction duration exceeded.')
        # P2 bounds response START. Once FF was accepted, N_Cr and the total
        # budget bound completion. Check before processing any newly queued FF.
        if self.deadline is not None and now >= self.deadline and not self.engine.receiving:
            return self.finish(Outcome.TIMEOUT,detail='Response Pending timed out.' if self.pending_count else 'No final ECU response within P2.')
        try:
            self.engine.process()
        except DiagnosticCancelled:
            return self.cancel()
        if self.engine.error is not None:
            return self.finish(Outcome.TIMEOUT if self.engine.timed_out else Outcome.ERROR,detail=str(self.engine.error))
        if self.deadline is None and not self.engine.transmitting:
            self.deadline=now+self.request.settings.p2_s
        payload=self.engine.receive()
        if payload is not None:
            if self.engine.transmitting or not response_belongs_to_request(self.request,payload): return None
            sid=self.request.uds_payload[0]
            if payload[:1] == b'\x7f':
                if len(payload) != 3:
                    return self.finish(Outcome.ERROR,payload,'Malformed UDS negative response.')
                if payload[1] != sid: return None
                nrc=payload[2]
                if nrc == 0x78:
                    self.pending_count+=1
                    self.pending_times.append(now-self.started)
                    self.deadline=now+self.request.settings.p2_star_s
                else:
                    return self.finish(Outcome.FAILED,payload,f'ECU terminal negative response NRC 0x{nrc:02X}; no security unlock attempted.',nrc)
            elif payload and payload[0] == sid+0x40:
                expected=self.request.expected
                outcome=(Outcome.NOT_EVALUATED if not expected else
                         Outcome.PASSED if (payload.startswith(expected) if self.request.match == 'prefix' else payload == expected) else Outcome.FAILED)
                return self.finish(outcome,payload,'Positive response; '+('no expected response specified.' if not expected else f'{self.request.match} expectation {outcome.value.lower()}.'))
        return self.result

    def finish(self, outcome, payload=None, detail='', nrc=None):
        if self.result is None:
            self.engine.stop()
            if self.cancelled.is_set():
                outcome,payload,detail,nrc=Outcome.CANCELLED,None,'Diagnostic request cancelled.',None
            self.result=DiagnosticResult(self.request,outcome,payload,detail,self.clock()-self.started,nrc,
                                         tuple(self.pending_times),self.pending_count)
        return self.result

    def cancel(self):
        self.cancelled.set()
        return self.finish(Outcome.CANCELLED,detail='Diagnostic request cancelled.')
