"""Opaque one-use generated-key capability. No provider/GUI dependency in core."""
from dataclasses import dataclass, field, fields
from math import isfinite
from threading import Event, RLock
import time
from uuid import uuid4

from core.diagnostic_request import DiagnosticRequest, DiagnosticValidationError as Invalid, is_security_seed_payload


@dataclass(frozen=True,repr=False)
class SecurityKeySubmission(DiagnosticRequest):
    capability: object = field(default=None,repr=False)
    _authority: object = field(default=None,repr=False)

    @property
    def requires_confirmation(self): return True

    def __repr__(self):
        return f'SecurityKeySubmission(transaction_id={self.transaction_id!r}, payload=<redacted>)'


def is_key_submission(request): return type(request) is SecurityKeySubmission


def validate_generated_constructor(request):
    if not is_key_submission(request) or type(request._authority) is not SubmissionAuthority:
        raise Invalid('Manual Security Access key payloads are disabled.')
    request._authority.validate_constructor(request)


class SubmissionAuthority:
    def __init__(self,proof_validator,*,clock=time.monotonic):
        self._validate_proof=proof_validator
        self._clock=clock
        self._records={}
        self._lock=RLock()

    def issue(self,seed_request,material,*,connection_id,epoch,authorization_id,deadline,cancel):
        with self._lock:
            for token,record in tuple(self._records.items()):
                if self._clock()>=record['deadline'] or record['cancel'].is_set():
                    del self._records[token]
            if (not is_security_seed_payload(seed_request.uds_payload) or len(self._records)>=32
                    or not self._validate_proof(material,seed_request.vehicle_name,seed_request.ecu_name,seed_request.transaction_id)
                    or not isinstance(connection_id,str) or not connection_id
                    or not isinstance(authorization_id,str) or not authorization_id
                    or type(epoch) is not int or epoch<0 or not isinstance(cancel,Event) or cancel.is_set()
                    or type(deadline) not in (int,float) or not isfinite(deadline)
                    or not self._clock()<deadline<=self._clock()+30):
                raise Invalid('Generated key has no current verified submission authority.')
            values={item.name:getattr(seed_request,item.name) for item in fields(DiagnosticRequest)}
            subfunc=seed_request.uds_payload[1]
            key_subfunc=subfunc+1
            values.update(transaction_id=uuid4().hex,uds_payload=bytes([0x27, key_subfunc])+material.key,
                          expected=bytes([0x67, key_subfunc]),match='exact',confirmed=True,bench_authorization_id='')
            token=object()
            self._records[token]=dict(values=values,material=material,seed_transaction=seed_request.transaction_id,
                connection=connection_id,epoch=epoch,authorization=authorization_id,deadline=deadline,
                cancel=cancel,claimed=False)
            try:
                return SecurityKeySubmission(**values,capability=token,_authority=self)
            except Exception:
                del self._records[token]
                raise

    def _record(self,request):
        record=self._records.get(getattr(request,'capability',None))
        if (not is_key_submission(request) or request._authority is not self or record is None
                or self._clock()>=record['deadline'] or record['cancel'].is_set()
                or any(getattr(request,name)!=value for name,value in record['values'].items())
                or not self._validate_proof(record['material'],request.vehicle_name,request.ecu_name,record['seed_transaction'])):
            raise Invalid('SecurityAccess capability expired, changed or untrusted.')
        return record

    def validate_constructor(self,request):
        with self._lock: self._record(request)

    def _check_owner(self,request,connection,epoch,authorization,simulator):
        record=self._record(request)
        if ((connection,epoch,authorization)!=(record['connection'],record['epoch'],record['authorization'])
                or (not record['material'].verified_real and simulator is not True)):
            raise Invalid('SecurityAccess owner/bench/session/provenance mismatch.')
        return record

    def claim(self,request,connection,epoch,authorization,*,simulator):
        with self._lock:
            record=self._check_owner(request,connection,epoch,authorization,simulator)
            if record['claimed']: raise Invalid('SecurityAccess capability was already consumed.')
            record['claimed']=True

    def check_active(self,request,connection,epoch,authorization,*,simulator):
        with self._lock:
            if not self._check_owner(request,connection,epoch,authorization,simulator)['claimed']:
                raise Invalid('SecurityAccess capability was not admitted by its owner.')

    def retire(self,request):
        with self._lock: self._records.pop(getattr(request,'capability',None),None)

    def revoke_all(self):
        with self._lock: self._records.clear()
