"""Expiring L1 lifecycle scaffold. Live submission stays closed pending ABI proof.

Reserved KEY_SUBMITTED/UNLOCKED states deliberately have no reachable transition:
this release has neither a validated real provider nor an admitted key request.
"""
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from threading import Event, RLock
import time

from core.diagnostic_request import DiagnosticOutcome, DiagnosticRequest, validate_send_policy
from services.can.security_seed_parser import parse_security_seed
from services.can.security_key_service import SecurityKeyService


class SecurityAccessBlocked(ValueError):
    pass


class SecurityAccessState(Enum):
    IDLE = 'Idle'
    SEED_REQUESTED = 'Seed requested'
    SEED_RECEIVED = 'Seed received'
    KEY_CALCULATED = 'Key calculated (offline mock)'
    KEY_SUBMITTED = 'Key submitted'
    UNLOCKED = 'Unlock successful'
    FAILED = 'Unlock failed'
    CANCELLED = 'Cancelled'


@dataclass(frozen=True)
class SecuritySessionIdentity:
    transaction_id: str
    step_id: str
    generation: int
    vehicle: str
    ecu: str
    tx_id: int
    rx_id: int
    subfunction: int
    connection_id: str
    session_epoch: int

    @classmethod
    def from_request(cls, request, connection_id, session_epoch):
        return cls(request.transaction_id, request.step_id, request.generation,
                   request.vehicle_name, request.ecu_name, request.tx_id, request.rx_id,
                   request.uds_payload[1], connection_id, session_epoch)


class SecurityAccessSession:
    def __init__(self, *, clock=time.monotonic, ttl_s=30):
        if type(ttl_s) not in (int, float) or not isfinite(ttl_s) or not 0 < ttl_s <= 30:
            raise ValueError('SecurityAccess material lifetime must be within 30 seconds.')
        self._clock, self._ttl = clock, ttl_s
        self._lock = RLock()
        self.state = SecurityAccessState.IDLE
        self.identity = None
        self._seed = self._key = None
        self._cancel = Event()
        self._calculating = False
        self._deadline = None

    @property
    def has_seed(self):
        with self._lock:
            self.expire()
            return self._seed is not None

    @property
    def status_text(self):
        with self._lock:
            self.expire()
            return f'{self.state.value}; 27 02 disabled: DLL ABI/offline verification pending.'

    def _clear(self):
        self._cancel.set()
        self._seed = self._key = None
        self.identity = self._deadline = None

    def invalidate(self):
        with self._lock:
            active = self.state != SecurityAccessState.IDLE
            self._clear()
            if active:
                self.state = SecurityAccessState.CANCELLED

    def expire(self):
        with self._lock:
            if self._deadline is not None and self._clock() >= self._deadline:
                self._clear()
                self.state = SecurityAccessState.FAILED

    def start(self, request, connection_id, session_epoch):
        with self._lock:
            self.expire()
            if self.state == SecurityAccessState.SEED_REQUESTED or self._calculating:
                raise SecurityAccessBlocked('A SecurityAccess operation is already running.')
            validate_send_policy(request)
            if (request.uds_payload != b'\x27\x01' or not isinstance(connection_id,str) or not connection_id
                    or type(session_epoch) is not int or session_epoch < 0):
                raise SecurityAccessBlocked('A connected Level 1 seed request is required.')
            self._clear()
            self._cancel = Event()
            self.identity = SecuritySessionIdentity.from_request(request, connection_id, session_epoch)
            self._deadline = self._clock()+request.settings.total_s
            self.state = SecurityAccessState.SEED_REQUESTED

    def _check(self, request, connection_id, session_epoch):
        self.expire()
        if (not isinstance(request,DiagnosticRequest) or request.uds_payload != b'\x27\x01'
                or self.identity is None or self.identity != SecuritySessionIdentity.from_request(request,connection_id,session_epoch)):
            self.invalidate()
            raise SecurityAccessBlocked('SecurityAccess context expired or changed.')

    def receive(self, result, connection_id, session_epoch):
        with self._lock:
            self._check(result.request,connection_id,session_epoch)
            if self.state != SecurityAccessState.SEED_REQUESTED:
                raise SecurityAccessBlocked('No seed request is awaiting a response.')
            if result.outcome == DiagnosticOutcome.CANCELLED:
                self.invalidate();return
            try:
                if result.outcome not in (DiagnosticOutcome.PASSED,DiagnosticOutcome.NOT_EVALUATED):
                    raise ValueError
                parsed = parse_security_seed(result.request.uds_payload, result.response_payload)
            except ValueError:
                self._clear()
                self.state = SecurityAccessState.FAILED
                return
            self._seed = parsed.seed
            self._deadline = self._clock()+self._ttl
            self.state = SecurityAccessState.SEED_RECEIVED

    def calculate_offline(self, provider, *, output_size):
        """Explicit mock/test API, never called automatically by a diagnostic result.

        A caller must run this blocking provider operation outside the GUI thread.
        Invalidation signals the process cancel Event and rejects a late result.
        """
        with self._lock:
            self.expire()
            if self.state != SecurityAccessState.SEED_RECEIVED or self._calculating:
                raise SecurityAccessBlocked('A current seed is required for offline calculation.')
            identity, seed, cancelled = self.identity, self._seed, self._cancel
            self._calculating = True
        try:
            result = SecurityKeyService(provider).calculate_from_response(vehicle=identity.vehicle,ecu=identity.ecu,
                request_payload=b'\x27\x01',response_payload=b'\x67\x01'+seed,output_size=output_size,cancel=cancelled)
            with self._lock:
                self.expire()
                if cancelled.is_set() or self.identity != identity:
                    raise SecurityAccessBlocked('Offline result belongs to an expired SecurityAccess context.')
                self._key = result.key
                self.state = SecurityAccessState.KEY_CALCULATED
                return result
        except Exception:
            with self._lock:
                if self.identity == identity:
                    self._clear()
                    self.state = SecurityAccessState.FAILED
            raise SecurityAccessBlocked('Offline key calculation failed or was cancelled; no key was submitted.') from None
        finally:
            with self._lock:
                self._calculating = False

    def prepare_submission(self, request, connection_id, session_epoch, *, authorized, confirmed):
        with self._lock:
            self._check(request,connection_id,session_epoch)
            if authorized is not True or confirmed is not True:
                raise SecurityAccessBlocked('An authorized bench and per-submission confirmation are required.')
            # Do not create a DiagnosticRequest or expose the mock key as manual text.
            raise SecurityAccessBlocked('Live 27 02 disabled: no ABI-verified, offline-validated real provider.')
