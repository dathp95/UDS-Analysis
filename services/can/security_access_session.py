"""Expiring L1 lifecycle. Only verified provenance can prepare an owner capability."""
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
    CALCULATING = 'Calculating key'
    KEY_CALCULATED = 'Key calculated (offline mock)'
    AWAITING_CONFIRMATION = 'Awaiting bench confirmation'
    KEY_SUBMITTED = 'Sending key'
    UNLOCKED = 'Security Unlocked (Level 1)'
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
        self._material=self._verified_gate=self._submission=self._authority=None
        self._already_unlocked = False
        self._simulated_unlock = False

    @property
    def has_seed(self):
        with self._lock:
            self.expire()
            return self._seed is not None

    @property
    def status_text(self):
        with self._lock:
            self.expire()
            if self._material is not None:
                label='Key calculated' if self.state==SecurityAccessState.KEY_CALCULATED else self.state.value
                return ('Simulator only: ' if not self._material.verified_real else '')+label
            if self.state==SecurityAccessState.UNLOCKED:
                prefix = 'Simulator only: ' if self._simulated_unlock else ''
                suffix = ' (already active; zero seed)' if self._already_unlocked else ''
                return prefix + self.state.value + suffix
            return self.state.value

    def _clear(self):
        if self._authority is not None and self._submission is not None:
            self._authority.retire(self._submission)
        self._material=self._verified_gate=self._submission=self._authority=None
        self._cancel.set()
        self._seed = self._key = None
        self.identity = self._deadline = None
        self._already_unlocked = False
        self._simulated_unlock = False

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
            if (request.uds_payload not in (b'\x27\x01', b'\x27\x03') or not isinstance(connection_id,str) or not connection_id
                    or type(session_epoch) is not int or session_epoch < 0):
                raise SecurityAccessBlocked('A connected Level 1/2 seed request is required.')
            self._clear()
            self._cancel = Event()
            self.identity = SecuritySessionIdentity.from_request(request, connection_id, session_epoch)
            self._deadline = self._clock()+request.settings.total_s
            self.state = SecurityAccessState.SEED_REQUESTED

    def _check(self, request, connection_id, session_epoch):
        self.expire()
        if (not isinstance(request,DiagnosticRequest) or request.uds_payload not in (b'\x27\x01', b'\x27\x03')
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
                parsed = parse_security_seed(result.request.uds_payload, result.response_payload, allow_l2=True)
                if not any(parsed.seed) and len(parsed.seed) != 16:
                    # Only the current 16-byte L1 profile can establish zero-seed
                    # semantics; a truncated/oversized response is not unlock proof.
                    raise ValueError
            except ValueError:
                self._clear()
                self.state = SecurityAccessState.FAILED
                return
            if not any(parsed.seed):
                # UDS: a zero seed reports this access level is already active.
                # Retain target identity so ECU/selection changes revoke the status.
                identity = self.identity
                self._clear()
                self.identity = identity
                self._already_unlocked = True
                self.state = SecurityAccessState.UNLOCKED
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
            req_payload = bytes([0x27, identity.subfunction])
            resp_payload = bytes([0x67, identity.subfunction]) + seed
            result = SecurityKeyService(provider).calculate_from_response(vehicle=identity.vehicle,ecu=identity.ecu,
                request_payload=req_payload,response_payload=resp_payload,output_size=output_size,cancel=cancelled)
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

    @property
    def can_calculate(self):
        with self._lock:
            self.expire()
            return self.state==SecurityAccessState.SEED_RECEIVED and self._seed is not None and len(self._seed)==16

    def calculate_verified(self,provider,gate):
        with self._lock:
            if not self.can_calculate or self._calculating:
                raise SecurityAccessBlocked('A current profile-compatible 16-byte seed is required.')
            identity,seed,cancel=self.identity,self._seed,self._cancel
            self._calculating=True
            self.state=SecurityAccessState.CALCULATING
        try:
            result=provider.calculate(seed,source_transaction=identity.transaction_id,cancel=cancel)
            with self._lock:
                self.expire()
                if (cancel.is_set() or self.identity!=identity
                        or not gate.validate(result,identity.vehicle,identity.ecu,identity.transaction_id)):
                    raise SecurityAccessBlocked('Untrusted or stale key calculation.')
                self._material,self._verified_gate=result,gate
                self.state=SecurityAccessState.KEY_CALCULATED
                return result
        except Exception:
            with self._lock:
                if self.identity==identity:
                    self._clear();self.state=SecurityAccessState.FAILED
            raise SecurityAccessBlocked('Key calculation failed or cancelled; nothing was submitted.') from None
        finally:
            with self._lock: self._calculating=False

    def await_confirmation(self):
        with self._lock:
            self.expire()
            if self.state!=SecurityAccessState.KEY_CALCULATED or self._material is None:
                raise SecurityAccessBlocked('No current verified key.')
            self.state=SecurityAccessState.AWAITING_CONFIRMATION

    def prepare_submission(self, request, connection_id, session_epoch, *, authorized, confirmed,
                           authority=None,owner_epoch=None,authorization_id=None):
        with self._lock:
            self._check(request,connection_id,session_epoch)
            if authorized is not True or confirmed is not True:
                raise SecurityAccessBlocked('An authorized bench and per-submission confirmation are required.')
            if (authority is None or self.state not in (SecurityAccessState.KEY_CALCULATED,SecurityAccessState.AWAITING_CONFIRMATION)
                    or self._material is None or self._verified_gate is None
                    or not self._verified_gate.validate(self._material,request.vehicle_name,request.ecu_name,request.transaction_id)):
                raise SecurityAccessBlocked('Live 27 02 disabled: no verified provider capability.')
            submission=authority.issue(request,self._material,connection_id=connection_id,epoch=owner_epoch,
                                       authorization_id=authorization_id,deadline=self._deadline,cancel=self._cancel)
            self._authority,self._submission=authority,submission
            self.state=SecurityAccessState.KEY_SUBMITTED
            return submission

    def finish_submission(self,result):
        with self._lock:
            self.expire()
            if self._submission is None or result.request is not self._submission:
                return False
            expected_pos = bytes([0x67, result.request.uds_payload[1]])
            success = result.outcome == DiagnosticOutcome.PASSED and result.response_payload == expected_pos
            identity = self.identity
            simulated = self._material is not None and not self._material.verified_real
            self._clear()
            if success:
                self.identity = identity
                self._simulated_unlock = simulated
            self.state=(SecurityAccessState.UNLOCKED if success else SecurityAccessState.CANCELLED
                        if result.outcome==DiagnosticOutcome.CANCELLED else SecurityAccessState.FAILED)
            return success
