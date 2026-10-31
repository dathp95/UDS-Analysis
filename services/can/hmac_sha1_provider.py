"""L1 HMAC and verification provenance. No OEM secret/profile is distributed.

Algorithm: supplied VinFast spec 3.8/3.9; Python 3.12 hmac (RFC2104).
Successful candidate comparison alone is NOT a physical-send authorization.
"""
from dataclasses import dataclass, field
import hashlib
import hmac
from threading import RLock
from types import MappingProxyType
from weakref import WeakKeyDictionary


class ProviderNotReady(ValueError):
    pass


def hmac_sha1_key(seed, secret):
    if not isinstance(seed,bytes) or len(seed)!=16 or not isinstance(secret,bytes) or len(secret)!=8:
        raise ValueError('L1 requires a 16-byte seed and 8-byte authorized secret.')
    return hmac.digest(secret,seed,'sha1')[:16]


@dataclass(frozen=True)
class OfflineVerification:
    total: int
    compared: int
    matched: int
    reason: str = ''

    @property
    def passed(self): return self.total>0 and self.total==self.compared==self.matched and not self.reason


def verify_offline_candidate(secret, vectors, *, ecu):
    vectors=tuple(vectors)
    if not isinstance(secret,bytes) or len(secret)!=8:
        return OfflineVerification(len(vectors),0,0,'Authorized secret unavailable.')
    if not vectors or len(vectors)>10000:
        return OfflineVerification(len(vectors),0,0,'No bounded reference set.')
    compared=matched=0
    for vector in vectors:
        if (vector.ecu!=ecu or vector.subfunction!=1 or not isinstance(vector.key,bytes)
                or len(vector.key)!=16 or not isinstance(vector.seed,bytes) or len(vector.seed)!=16):
            return OfflineVerification(len(vectors),compared,matched,'Reference identity/length mismatch.')
        compared+=1
        if not hmac.compare_digest(hmac_sha1_key(vector.seed,secret),vector.key):
            return OfflineVerification(len(vectors),compared,matched,'Reference mismatch; stopped.')
        matched+=1
    return OfflineVerification(len(vectors),compared,matched)


# Reviewed release registrations only. No GUI/config/env may populate this table.
# A registration must bind vehicle, ECU, source_id, revision, vector_sha256/count.
# No OEM-approved secret source or applicable profile has been supplied.
APPROVED_HMAC_PROFILES=MappingProxyType({})


@dataclass(frozen=True,eq=False)
class _ProviderProof:
    vehicle: str
    ecu: str
    fingerprint: str
    verified_real: bool


@dataclass(frozen=True,eq=False,repr=False)
class KeyMaterial:
    vehicle: str
    ecu: str
    source_transaction: str
    fingerprint: str
    verified_real: bool
    key: bytes = field(repr=False)
    _proof: object = field(repr=False)

    def __repr__(self):
        return f'KeyMaterial(key_length={len(self.key)}, verified_real={self.verified_real})'


class _HmacProvider:
    def __init__(self, gate, proof, secret):
        self._gate,self._proof,self._secret=gate,proof,secret

    def calculate(self, seed, *, source_transaction, cancel=None):
        if not isinstance(source_transaction,str) or not 0<len(source_transaction)<=128:
            raise ProviderNotReady('Seed transaction identity is required.')
        if cancel is not None and cancel.is_set(): raise ProviderNotReady('Calculation cancelled.')
        key=hmac_sha1_key(seed,self._secret)
        if cancel is not None and cancel.is_set(): raise ProviderNotReady('Calculation cancelled.')
        proof=self._proof
        result=KeyMaterial(proof.vehicle,proof.ecu,source_transaction,proof.fingerprint,
                           proof.verified_real,key,proof)
        return self._gate._record(result)


class RealSeedKeyProvider(_HmacProvider):
    """Only a gate-issued, offline-verified registration can construct this provider."""
    def __init__(self,gate,proof,secret):
        if (not isinstance(gate,ProviderVerificationGate) or proof not in gate._proofs
                or not proof.verified_real or not isinstance(secret,bytes) or len(secret)!=8):
            raise ProviderNotReady('No approved, verified real Seed-Key provider.')
        super().__init__(gate,proof,secret)


class _DllProvider:
    def __init__(self, gate, proof, dll_path, subfunction=1):
        self._gate, self._proof, self._dll_path, self._subfunction = gate, proof, dll_path, subfunction

    def calculate(self, seed, *, source_transaction, cancel=None):
        if not isinstance(source_transaction, str) or not 0 < len(source_transaction) <= 128:
            raise ProviderNotReady('Seed transaction identity is required.')
        if cancel is not None and cancel.is_set():
            raise ProviderNotReady('Calculation cancelled.')
        key = self._calculate_native(seed, cancel=cancel)
        if cancel is not None and cancel.is_set():
            raise ProviderNotReady('Calculation cancelled.')
        proof = self._proof
        result = KeyMaterial(proof.vehicle, proof.ecu, source_transaction, proof.fingerprint,
                           proof.verified_real, key, proof)
        return self._gate._record(result)

    def _calculate_native(self, seed, cancel=None):
        from pathlib import Path
        from services.can.seed_key_worker import ProcessWorkerTransport
        from services.seed_key_provider import SeedKeyRequest, encode_request, decode_response
        worker_exe = Path(__file__).resolve().parents[2] / 'build' / 'security_worker' / 'SeedKeyWorker.x86.exe'
        if not worker_exe.is_file():
            worker_exe = Path('build/security_worker/SeedKeyWorker.x86.exe').resolve()
        if not worker_exe.is_file():
            raise ProviderNotReady('SeedKeyWorker.x86.exe is not available.')
        transport = ProcessWorkerTransport([str(worker_exe), '--mock'])
        try:
            req = SeedKeyRequest(
                request_id='dll_req',
                vehicle=self._proof.vehicle,
                ecu=self._proof.ecu,
                level=self._subfunction,
                seed=seed,
                output_size=16,
                timeout_s=2.0,
                dll_path=self._dll_path,
            )
            payload = encode_request(req)
            resp_bytes = transport.exchange(payload, timeout_s=2.0, cancel=cancel)
            resp = decode_response(resp_bytes, req)
            return resp.key
        finally:
            transport.close()


class ProviderVerificationGate:
    def __init__(self, *, simulator=False):
        self._simulator=simulator is True
        self._proofs=set()
        self._providers={}
        self._materials=WeakKeyDictionary()
        self._lock=RLock()

    def register_dll_provider(self, vehicle, ecu, dll_path, subfunction=1):
        with self._lock:
            key = (vehicle, ecu, subfunction)
            proof = _ProviderProof(vehicle, ecu, f'x86-dll-{subfunction}:{dll_path}', True)
            self._proofs.add(proof)
            provider = _DllProvider(self, proof, dll_path, subfunction=subfunction)
            self._providers[key] = provider
            if (vehicle, ecu) not in self._providers or not self._simulator:
                self._providers[(vehicle, ecu)] = provider
            return provider

    def provider(self,vehicle,ecu,subfunction=1):
        with self._lock:
            key_sub=(vehicle,ecu,subfunction)
            if key_sub in self._providers:
                return self._providers[key_sub]
            key=(vehicle,ecu)
            if key in self._providers:
                return self._providers[key]
            if self._simulator:
                proof=_ProviderProof(vehicle,ecu,'simulator-public-hmac-sha1-128-v1',False)
                self._proofs.add(proof)
                self._providers[key]=_HmacProvider(self,proof,b'SIMUL8!!')  # PUBLIC SIMULATOR ONLY
                return self._providers[key]
            return None

    def _record(self,result):
        with self._lock:
            if result._proof not in self._proofs:
                raise ProviderNotReady('Untrusted provider provenance.')
            self._materials[result]=result._proof
            return result

    def validate(self,result,vehicle,ecu,source_transaction):
        with self._lock:
            if type(result) is not KeyMaterial or result not in self._materials:
                return False
            proof=self._materials[result]
            return (result._proof is proof and proof in self._proofs
                    and (result.vehicle,result.ecu,result.source_transaction)==(vehicle,ecu,source_transaction)
                    and result.fingerprint==proof.fingerprint and result.verified_real is proof.verified_real
                    and isinstance(result.key,bytes) and len(result.key)==16
                    and (proof.verified_real or self._simulator))

    def verify_approved_profile(self,profile_id,secret_source,vectors):
        registration=APPROVED_HMAC_PROFILES.get(profile_id)
        if registration is None or self._simulator:
            raise ProviderNotReady('OEM profile, secret source and applicability approval are missing.')
        vectors=tuple(vectors)
        digest=hashlib.sha256(b''.join(v.seed+v.key for v in vectors)).hexdigest()
        if len(vectors)!=registration['count'] or digest!=registration['vector_sha256']:
            raise ProviderNotReady('Approved reference set does not match.')
        try:
            secret=secret_source(registration['source_id'])
            report=verify_offline_candidate(secret,vectors,ecu=registration['ecu'])
        except Exception:
            raise ProviderNotReady('Authorized offline verification failed.') from None
        if not report.passed: raise ProviderNotReady('Authorized offline vectors did not match.')
        fingerprint=f"{profile_id}:{registration['revision']}:{digest}"
        proof=_ProviderProof(registration['vehicle'],registration['ecu'],fingerprint,True)
        with self._lock:
            self._proofs.add(proof)
            provider=RealSeedKeyProvider(self,proof,secret)
            self._providers[(proof.vehicle,proof.ecu)]=provider
        return provider,report
