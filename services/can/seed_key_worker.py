"""One-shot bounded pipe transport. No DLL is loaded into the Python/Qt process."""
import math
import os
import queue
import struct
import subprocess
import signal
from threading import Event, Lock, Thread
import time

from services.seed_key_provider import (MAX_IPC_BYTES, ProviderError, ProviderErrorCode as Code,
                                       encode_request, decode_response)


class ProcessWorkerTransport:
    def __init__(self, command):
        if not isinstance(command,(list,tuple)) or not command or not all(isinstance(item, str) and item for item in command):
            raise ValueError('Worker command must be an explicit argument list.')
        self._command = tuple(command)
        self._operation, self._state = Lock(), Lock()
        self._closed = Event()
        self._process = None

    @property
    def active_pid(self):
        with self._state:
            return self._process.pid if self._process is not None else None

    @staticmethod
    def _read(stream, size):
        result = bytearray()
        while len(result) < size:
            part = stream.read(size-len(result))
            if not part:
                break
            result.extend(part)
        return bytes(result)

    def exchange(self, payload, *, timeout_s, cancel):
        if (not isinstance(payload, bytes) or not 0 < len(payload) <= MAX_IPC_BYTES
                or type(timeout_s) not in (int, float) or not math.isfinite(timeout_s)
                or not .001 <= timeout_s <= 30):
            raise ProviderError(Code.BAD_REQUEST)
        if not self._operation.acquire(blocking=False):
            raise ProviderError(Code.UNAVAILABLE)
        process, io_thread, job = None, None, None
        deadline = time.monotonic()+timeout_s
        try:
            with self._state:
                if self._closed.is_set() or (cancel is not None and cancel.is_set()):
                    raise ProviderError(Code.CANCELLED)
                try:
                    if os.name == 'nt':
                        from services.can.windows_worker_job import WindowsWorkerJob
                        job=WindowsWorkerJob()
                    # No shell or secret arguments/files. Worker stderr is never forwarded.
                    process = subprocess.Popen(self._command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                               stderr=subprocess.DEVNULL, bufsize=0,
                                               creationflags=(getattr(subprocess, 'CREATE_NO_WINDOW', 0)|0x4) if job else 0,
                                               start_new_session=os.name != 'nt')
                    if job is not None:
                        job.attach_and_resume(process.pid)
                except OSError:
                    raise ProviderError(Code.UNAVAILABLE) from None
                self._process = process
            completed = queue.Queue(maxsize=1)
            def communicate_bounded():
                try:
                    frame = struct.pack('<I', len(payload))+payload
                    written = 0
                    while written < len(frame):
                        count = process.stdin.write(frame[written:])
                        if not count:
                            raise OSError
                        written += count
                    process.stdin.close()
                    header = self._read(process.stdout, 4)
                    if len(header) != 4:
                        completed.put(('short', None));return
                    size = struct.unpack('<I', header)[0]
                    if not 0 < size <= MAX_IPC_BYTES:
                        completed.put(('bad', None));return
                    response = self._read(process.stdout, size)
                    if len(response) != size or process.stdout.read(1):
                        completed.put(('bad', None));return
                    completed.put(('ok', response))
                except (OSError, ValueError):
                    completed.put(('short', None))
            io_thread = Thread(target=communicate_bounded, name='seed-key-pipe', daemon=True)
            io_thread.start()
            result = None
            while True:
                if self._closed.is_set() or (cancel is not None and cancel.is_set()):
                    raise ProviderError(Code.CANCELLED)
                if time.monotonic() >= deadline:
                    raise ProviderError(Code.TIMEOUT)
                if result is None:
                    try:
                        result = completed.get(timeout=min(.01, max(0, deadline-time.monotonic())))
                    except queue.Empty:
                        continue
                status, response = result
                if status == 'bad':
                    raise ProviderError(Code.BAD_RESPONSE)
                exit_code = process.poll()
                if exit_code is None:
                    self._closed.wait(.002)
                    continue
                if exit_code:
                    raise ProviderError(Code.WORKER_CRASH)
                if status != 'ok':
                    raise ProviderError(Code.BAD_RESPONSE)
                return response
        finally:
            cleanup_failed=False
            try:
                try:
                    if job is not None:
                        job.close()  # Kill descendants holding inherited pipe handles as well.
                    elif process is not None and os.name != 'nt':
                        try: os.killpg(process.pid,signal.SIGKILL)
                        except ProcessLookupError: pass
                except OSError:
                    cleanup_failed=True
                if process is not None:
                    try:
                        if process.poll() is None:
                            process.kill()
                        process.wait(timeout=.5)
                    except (OSError,subprocess.TimeoutExpired):
                        cleanup_failed=True
                    if io_thread is not None:
                        io_thread.join(timeout=.5)
                    if io_thread is not None and io_thread.is_alive():
                        # Never call close() over another thread's blocking read.
                        cleanup_failed=True
                    else:
                        for stream in (process.stdin,process.stdout):
                            stream.close()
            finally:
                with self._state:
                    self._process = None
                self._operation.release()
            if cleanup_failed:
                raise ProviderError(Code.WORKER_CRASH) from None

    def close(self):
        """Interrupt an active exchange; exchange's finally block reaps the child."""
        self._closed.set()


class ProcessMockSeedKeyProvider:
    """Explicit mock adapter. Its response can never authorize ECU key submission."""
    def __init__(self, transport):
        self.transport = transport

    def calculate(self, request, *, cancel=None):
        payload = encode_request(request)
        response = self.transport.exchange(payload, timeout_s=request.timeout_s, cancel=cancel)
        return decode_response(response, request)
