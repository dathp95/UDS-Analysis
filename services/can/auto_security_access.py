"""One logical L1 row, two independent UDS transactions. No I/O or Qt ownership."""
from dataclasses import dataclass, replace
from uuid import uuid4
import time

from core.diagnostic_request import DiagnosticOutcome as Outcome
from core.security_submission import is_key_submission


@dataclass(frozen=True)
class AutoSecurityResult:
    outcome: Outcome
    response: bytes
    detail: str


@dataclass(frozen=True)
class AutoPhysicalRecord:
    transaction_id: str
    phase: str
    outcome: Outcome
    elapsed_s: float
    nrc: int | None


class AutoSecurityAccessL1:
    """Composite protocol state; trace deliberately excludes requests/seed/key."""
    def __init__(self, logical_request, *, clock=time.monotonic):
        if not self.matches(logical_request):
            raise ValueError('Auto L1 requires exact 27 01 and final expected 67 02.')
        self.logical_request = logical_request
        self.workflow_id = uuid4().hex
        self._clock = clock
        self.deadline = clock() + logical_request.settings.total_s
        self.seed_request = replace(logical_request, transaction_id=uuid4().hex,
                                    expected=b'\x67\x01', match='prefix', confirmed=True)
        self.key_request = None
        self.phase = 'Requesting seed'
        self.result = None
        self.trace = []

    @staticmethod
    def matches(request):
        return request.uds_payload == b'\x27\x01' and request.expected == b'\x67\x02'

    @property
    def expired(self):
        return self._clock() >= self.deadline

    def _record(self, result):
        self.trace.append(AutoPhysicalRecord(result.request.transaction_id, self.phase,
            result.outcome, result.elapsed_s, result.nrc))

    def finish(self, outcome, response=b'', detail=''):
        if self.result is None:
            self.result = AutoSecurityResult(outcome, response, detail)
            self.phase = 'Finished'

    def accept_seed(self, result):
        if self.result is not None or self.phase != 'Requesting seed' or result.request is not self.seed_request:
            return False
        self._record(result)
        if result.outcome not in (Outcome.PASSED, Outcome.NOT_EVALUATED):
            self.finish(result.outcome, self._safe_response(result), 'Seed request: ' + result.detail)
            return False
        payload = result.response_payload
        if not isinstance(payload, bytes) or len(payload) != 18 or payload[:2] != b'\x67\x01':
            self.finish(Outcome.ERROR, detail='Seed response must be 67 01 plus the current profile\'s 16 bytes.')
            return False
        if not any(payload[2:]):
            self.finish(Outcome.NOT_EVALUATED, b'\x67\x01',
                'Already unlocked (zero seed); no key sent and no 67 02 received.')
            return False
        self.phase = 'Seed received'
        return True

    def calculating(self):
        if self.phase != 'Seed received' or self.result is not None:
            raise ValueError('No accepted seed for Auto L1 calculation.')
        self.phase = 'Calculating key'

    def key_ready(self, request):
        if (self.result is not None or self.phase not in ('Seed received', 'Calculating key')
                or not is_key_submission(request)
                or (request.vehicle_name, request.ecu_name, request.tx_id, request.rx_id,
                    request.step_id, request.generation) !=
                   (self.seed_request.vehicle_name, self.seed_request.ecu_name,
                    self.seed_request.tx_id, self.seed_request.rx_id,
                    self.seed_request.step_id, self.seed_request.generation)):
            raise ValueError('Generated key does not belong to the Auto L1 workflow.')
        self.key_request = request
        self.phase = 'Waiting for ECU'

    def accept_key(self, result, *, accepted):
        if self.result is not None or self.phase != 'Waiting for ECU' or result.request is not self.key_request:
            return False
        self._record(result)
        success = accepted is True and result.outcome == Outcome.PASSED and result.response_payload == b'\x67\x02'
        outcome = Outcome.PASSED if success else Outcome.ERROR if result.outcome == Outcome.PASSED else result.outcome
        detail = 'Security Unlocked (Level 1)' if success else 'Key request: ' + result.detail
        self.finish(outcome, b'\x67\x02' if success else self._safe_response(result), detail)
        return success

    @staticmethod
    def _safe_response(result):
        payload = result.response_payload
        return payload if isinstance(payload, bytes) and len(payload) == 3 and payload[:2] == b'\x7f\x27' else b''
