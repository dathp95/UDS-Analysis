"""Mock-only provider and bounded IPC contract. No DLL, CAN or UDS execution path.

The fake worker exercises serialization/error handling in memory. A future isolated
x86 executable must implement WorkerTransport after separate ABI authorization.
Never log request/response wire payloads: they contain sensitive material.
"""
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import math
import re
from threading import Event
import time
from typing import Protocol

MAX_IPC_BYTES = 4096
MAX_SEED_BYTES = 64
MAX_KEY_BYTES = 64


class ProviderErrorCode(Enum):
    BAD_REQUEST = 'bad_request'
    BAD_RESPONSE = 'bad_response'
    TIMEOUT = 'timeout'
    CANCELLED = 'cancelled'
    WORKER_CRASH = 'worker_crash'
    UNAVAILABLE = 'unavailable'


class ProviderError(ValueError):
    def __init__(self, code: ProviderErrorCode):
        self.code = code
        super().__init__(f'Mock provider failed: {code.value}. No Security Access was performed.')


@dataclass(frozen=True)
class SeedKeyRequest:
    request_id: str
    vehicle: str
    ecu: str
    level: int
    seed: bytes = field(repr=False)
    output_size: int = 16
    timeout_s: float = 1.0


@dataclass(frozen=True)
class SeedKeyResponse:
    request_id: str
    key: bytes = field(repr=False)
    mock_only: bool = True


class SeedKeyProvider(Protocol):
    def calculate(self, request: SeedKeyRequest, *, cancel: Event | None = None) -> SeedKeyResponse: ...


class WorkerTransport(Protocol):
    """Future process adapter: bounded frame, hard deadline, cancellation and reap-on-crash."""
    def exchange(self, payload: bytes, *, timeout_s: float, cancel: Event | None) -> bytes: ...


def _validate(request):
    valid_name = lambda name: isinstance(name, str) and 0 < len(name) <= 128 and name.isprintable()
    if (not isinstance(request.request_id, str) or re.fullmatch(r'[A-Za-z0-9_-]{1,64}', request.request_id) is None
            or not valid_name(request.vehicle) or not valid_name(request.ecu)
            or type(request.level) is not int or not 1 <= request.level <= 0x7F
            or not isinstance(request.seed, bytes) or not 1 <= len(request.seed) <= MAX_SEED_BYTES
            or type(request.output_size) is not int or not 1 <= request.output_size <= MAX_KEY_BYTES
            or type(request.timeout_s) not in (int, float) or not math.isfinite(request.timeout_s)
            or not .001 <= request.timeout_s <= 30):
        raise ProviderError(ProviderErrorCode.BAD_REQUEST)


def _encode(value):
    payload = json.dumps(value, separators=(',', ':'), ensure_ascii=True).encode('ascii')
    if len(payload) > MAX_IPC_BYTES:
        raise ProviderError(ProviderErrorCode.BAD_REQUEST)
    return payload


def _decode(payload, code):
    def unique_fields(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError
            result[key] = value
        return result
    try:
        if not isinstance(payload, bytes) or not 0 < len(payload) <= MAX_IPC_BYTES:
            raise ValueError
        value = json.loads(payload, object_pairs_hook=unique_fields)
        if not isinstance(value, dict):
            raise ValueError
        return value
    except (ValueError, UnicodeError, RecursionError):
        raise ProviderError(code) from None


def encode_request(request: SeedKeyRequest) -> bytes:
    _validate(request)
    return _encode(dict(version=1, request_id=request.request_id, vehicle=request.vehicle,
                        ecu=request.ecu, level=request.level, seed_hex=request.seed.hex(),
                        output_size=request.output_size, timeout_ms=int(request.timeout_s*1000)))


def decode_request(payload: bytes) -> SeedKeyRequest:
    value = _decode(payload, ProviderErrorCode.BAD_REQUEST)
    try:
        if set(value) != {'version','request_id','vehicle','ecu','level','seed_hex','output_size','timeout_ms'}:
            raise ValueError
        if type(value['version']) is not int or value['version'] != 1 or type(value['timeout_ms']) is not int:
            raise ValueError
        seed = value['seed_hex']
        if not isinstance(seed, str) or len(seed) > 2*MAX_SEED_BYTES or re.fullmatch(r'(?:[0-9a-fA-F]{2})+', seed) is None:
            raise ValueError
        request = SeedKeyRequest(value['request_id'],value['vehicle'],value['ecu'],value['level'],
                                 bytes.fromhex(seed),value['output_size'],value['timeout_ms']/1000)
        _validate(request)
        return request
    except (ValueError, KeyError, TypeError):
        raise ProviderError(ProviderErrorCode.BAD_REQUEST) from None


def decode_response(payload: bytes, request: SeedKeyRequest) -> SeedKeyResponse:
    _validate(request)
    value = _decode(payload, ProviderErrorCode.BAD_RESPONSE)
    try:
        if (type(value['version']) is not int or value['version'] != 1
                or value['request_id'] != request.request_id or value['mock_only'] is not True):
            raise ValueError
        if value['status'] == 'error':
            if set(value) != {'version','request_id','status','error_code','mock_only'}:
                raise ValueError
            raise ProviderError(ProviderErrorCode(value['error_code']))
        if value['status'] != 'ok' or set(value) != {'version','request_id','status','key_hex','mock_only'}:
            raise ValueError
        key = value['key_hex']
        if not isinstance(key, str) or len(key) != 2*request.output_size or re.fullmatch(r'[0-9a-fA-F]+',key) is None:
            raise ValueError
        return SeedKeyResponse(request.request_id, bytes.fromhex(key))
    except ProviderError:
        raise
    except (ValueError, KeyError, TypeError):
        raise ProviderError(ProviderErrorCode.BAD_RESPONSE) from None


class _MockWorker:
    def __init__(self, delay_s=0, crash=False):
        self.delay_s, self.crash = delay_s, crash

    def exchange(self, payload, *, timeout_s, cancel):
        request = decode_request(payload)
        started = time.monotonic()
        while True:
            if cancel is not None and cancel.is_set():
                raise ProviderError(ProviderErrorCode.CANCELLED)
            elapsed = time.monotonic()-started
            if elapsed >= timeout_s:
                raise ProviderError(ProviderErrorCode.TIMEOUT)
            if self.crash:
                raise ProviderError(ProviderErrorCode.WORKER_CRASH)
            if elapsed >= self.delay_s:
                break
            (cancel or Event()).wait(min(.005, self.delay_s-elapsed, timeout_s-elapsed))
        material = b'V-CODE M05B TEST ONLY\0'+request.vehicle.encode()+b'\0'+request.ecu.encode()+bytes([request.level])+request.seed
        key = (hashlib.sha256(material).digest()*2)[:request.output_size]
        return _encode(dict(version=1,request_id=request.request_id,status='ok',key_hex=key.hex(),mock_only=True))


class MockSeedKeyProvider:
    """Deterministic test double, independent of process architecture; never a DLL adapter."""
    def __init__(self, *, delay_s=0, crash=False):
        self._worker = _MockWorker(delay_s, crash)

    def calculate(self, request: SeedKeyRequest, *, cancel: Event | None = None) -> SeedKeyResponse:
        payload = encode_request(request)
        response = self._worker.exchange(payload, timeout_s=request.timeout_s, cancel=cancel)
        return decode_response(response, request)
