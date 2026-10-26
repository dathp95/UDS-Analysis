"""Independent bounded recorder. Its single file owner never touches the CAN bus."""
from dataclasses import dataclass, replace
from collections import deque
from math import isfinite
from pathlib import Path
from queue import Queue, Empty, Full
from threading import Event, RLock, Thread

from core.can_interface_view import CanFrameView


@dataclass(frozen=True)
class RecordingSnapshot:
    state: str = 'STOPPED'
    path: str = ''
    captured: int = 0
    written: int = 0
    dropped: int = 0
    echoes: int = 0
    adjusted_timestamps: int = 0
    fallback_timestamps: int = 0
    error: str = ''
    finalized: bool = False
    busy: bool = False

    @property
    def complete(self):
        return self.finalized and not self.busy and not self.error and self.dropped == 0 and self.captured == self.written


def to_blf_message(frame):
    import can
    if not isinstance(frame,CanFrameView): raise ValueError('Invalid raw CAN event.')
    if (frame.wall_timestamp_s is None or not isfinite(frame.wall_timestamp_s)
            or not 946684800 <= frame.wall_timestamp_s <= 4102444800):
        raise ValueError('No usable Unix timestamp for BLF recording.')
    if isinstance(frame.channel,bool) or not isinstance(frame.channel,int) or not 0 <= frame.channel < 65535:
        raise ValueError('Cannot map selected local CAN port to a BLF channel.')
    # python-can 4.6.1 CAN_ERROR_EXT does not serialize TX direction. Refuse a
    # lossy conversion rather than silently label an outgoing error as RX.
    if frame.is_error_frame and frame.direction != 'RX':
        raise ValueError('BLF cannot preserve TX error-frame direction.')
    return can.Message(timestamp=frame.wall_timestamp_s,arbitration_id=frame.can_id,
        is_extended_id=frame.is_extended_id,is_remote_frame=frame.is_remote_frame,
        is_error_frame=frame.is_error_frame,dlc=frame.dlc,data=frame.data,
        channel=frame.channel,is_rx=frame.direction=='RX',check=True)


class BlfRecordingService:
    def __init__(self,capacity=32768,writer_factory=None):
        if isinstance(capacity,bool) or not isinstance(capacity,int) or capacity<1:
            raise ValueError('Recording queue capacity must be positive.')
        self.capacity=capacity
        self._factory=writer_factory
        self._lock=RLock()
        self._snapshot=RecordingSnapshot()
        self._done=Event();self._done.set()
        self._stop=Event()
        self._thread=None

    @property
    def snapshot(self):
        with self._lock: return self._snapshot

    def _change(self,**values):
        self._snapshot=replace(self._snapshot,**values)

    def start(self,path,session_id,*,overwrite=False):
        path=Path(path)
        if path.suffix.lower() != '.blf' or not session_id:
            raise ValueError('Choose a .blf destination and an active CAN session.')
        with self._lock:
            if not self._done.is_set(): raise RuntimeError('A BLF writer is already active or finalizing.')
            self._queue=Queue(self.capacity)
            self._session_id=session_id
            self._last_sequence=0
            self._last_wall=None
            self._accepted_tx=deque(maxlen=256)
            self._stop=Event();self._done=Event()
            self._snapshot=RecordingSnapshot('STARTING',str(path),busy=True)
            self._thread=Thread(target=self._write,args=(path,overwrite),name='VCode-BLF-writer',daemon=False)
            try: self._thread.start()
            except Exception as error:
                self._change(state='INCOMPLETE',error=str(error),busy=False)
                self._done.set()
                raise

    def offer(self,frame):
        """Called directly by the acquisition owner; never waits for disk/GUI."""
        with self._lock:
            if self._snapshot.state not in ('STARTING','RECORDING'): return
            if frame.echo_of_sequence is not None and frame.echo_of_sequence in self._accepted_tx:
                self._change(echoes=self._snapshot.echoes+1)
                return
            self._change(captured=self._snapshot.captured+1)
            try:
                if frame.session_id != self._session_id or frame.sequence <= self._last_sequence:
                    raise ValueError('Stale/misordered CAN connection event.')
                if frame.wall_timestamp_s is None or (self._last_wall is not None and frame.wall_timestamp_s < self._last_wall):
                    raise ValueError('Missing or decreasing canonical timestamp.')
                self._queue.put_nowait(frame)
                self._last_sequence=frame.sequence
                self._last_wall=frame.wall_timestamp_s
                if frame.tx_origin=='driver_accepted': self._accepted_tx.append(frame.sequence)
                self._change(adjusted_timestamps=self._snapshot.adjusted_timestamps+int('clamped' in frame.timestamp_source),
                             fallback_timestamps=self._snapshot.fallback_timestamps+int('fallback' in frame.timestamp_source))
            except (ValueError,Full) as error:
                reason='Recording queue overflow; capture is incomplete.' if isinstance(error,Full) else str(error)
                self._change(dropped=self._snapshot.dropped+1)
                self._fail(reason)

    def _fail(self,reason):
        self._change(state='INCOMPLETE',error=self._snapshot.error or reason)
        self._stop.set()

    def stop(self,reason=''):
        """Acceptance boundary is protected by the same lock as offer()."""
        with self._lock:
            if self._done.is_set(): return
            if reason: self._fail(reason)
            elif self._snapshot.state != 'INCOMPLETE': self._change(state='STOPPING')
            self._stop.set()

    def wait(self,timeout=None):
        return self._done.wait(timeout)

    def _write(self,path,overwrite):
        writer=None
        handle=None
        finalized=False
        failed_write=False
        try:
            factory=self._factory
            if factory is None:
                from can import BLFWriter
                factory=BLFWriter
            # Exclusive creation prevents a race with another recorder/process.
            # Existing files are truncated only after explicit GUI confirmation.
            handle=path.open('wb+' if overwrite else 'xb+')
            writer=factory(handle,append=False)
            with self._lock:
                if self._snapshot.state=='STARTING': self._change(state='RECORDING')
            while not self._stop.is_set() or not self._queue.empty():
                try: frame=self._queue.get(timeout=.05)
                except Empty: continue
                try:
                    if failed_write: raise RuntimeError('Previous BLF write failed.')
                    writer.on_message_received(to_blf_message(frame))
                    with self._lock: self._change(written=self._snapshot.written+1)
                except Exception as error:
                    failed_write=True
                    with self._lock:
                        self._change(dropped=self._snapshot.dropped+1)
                        self._fail(f'BLF write failed: {error}')
        except Exception as error:
            with self._lock: self._fail(f'BLF open/write failed: {error}')
        finally:
            if writer is not None:
                try:
                    writer.stop()  # Exactly once, including write-error paths.
                    finalized=True
                except Exception as error:
                    with self._lock: self._fail(f'BLF finalization failed: {error}')
            if handle is not None and not handle.closed:
                try: handle.close()
                except Exception as error:
                    finalized=False
                    with self._lock: self._fail(f'BLF close failed: {error}')
            with self._lock:
                remaining=self._queue.qsize()
                self._change(dropped=self._snapshot.dropped+remaining,finalized=finalized,
                    state='INCOMPLETE' if self._snapshot.error else 'STOPPED',busy=False)
                self._done.set()
