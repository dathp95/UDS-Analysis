import unittest
from dataclasses import replace
from threading import Event

from services.can.hmac_sha1_provider import (hmac_sha1_key, verify_offline_candidate,
    ProviderVerificationGate, RealSeedKeyProvider, ProviderNotReady)
from services.can.security_reference import SecurityReferenceVector


class HmacProviderTests(unittest.TestCase):
    def test_public_dummy_vector_and_lengths(self):
        # Independent .NET HMACSHA1 result, public SIMUL8!! key, seed bytes 00..0F.
        result=hmac_sha1_key(bytes(range(16)),b'SIMUL8!!')
        self.assertEqual(result.hex(),'850621424d630dbe293ced578ca3a104')
        for seed,secret in ((b'',b'SIMUL8!!'),(bytes(15),b'SIMUL8!!'),(bytes(17),b'SIMUL8!!'),
                            (bytes(16),bytes(7)),(bytes(16),bytes(9))):
            with self.assertRaises(ValueError): hmac_sha1_key(seed,secret)

    def test_offline_comparison_is_not_authorization_and_stops_on_mismatch(self):
        seed=bytes(range(16));key=hmac_sha1_key(seed,b'SIMUL8!!')
        vector=SecurityReferenceVector('BCM',1,1,1,2,seed,key)
        report=verify_offline_candidate(b'SIMUL8!!',[vector,vector],ecu='BCM')
        self.assertTrue(report.passed)
        self.assertEqual((report.compared,report.matched),(2,2))
        failed=verify_offline_candidate(b'SIMUL8!!',[replace(vector,key=bytes(16)),vector],ecu='BCM')
        self.assertFalse(failed.passed);self.assertEqual(failed.compared,1)
        for vectors in ([],[replace(vector,subfunction=3)],[replace(vector,ecu='EPS')]):
            self.assertFalse(verify_offline_candidate(b'SIMUL8!!',vectors,ecu='BCM').passed)

    def test_proof_bound_to_gate_target_seed_transaction_and_cancellation(self):
        gate=ProviderVerificationGate(simulator=True)
        provider=gate.provider('SIM','BCM')
        material=provider.calculate(bytes(range(16)),source_transaction='seed-tx')
        self.assertTrue(gate.validate(material,'SIM','BCM','seed-tx'))
        self.assertFalse(material.verified_real)
        self.assertFalse(ProviderVerificationGate().validate(material,'SIM','BCM','seed-tx'))
        self.assertFalse(gate.validate(material,'SIM','EPS','seed-tx'))
        self.assertFalse(gate.validate(material,'SIM','BCM','other-seed'))
        self.assertFalse(gate.validate(replace(material,key=b''),'SIM','BCM','seed-tx'))
        cancel=Event();cancel.set()
        with self.assertRaises(ValueError): provider.calculate(bytes(16),source_transaction='tx',cancel=cancel)
        self.assertNotIn(material.key.hex(),repr(material))

    def test_no_approved_real_profile_and_boolean_metadata_do_not_authorize(self):
        gate=ProviderVerificationGate()
        self.assertIsNone(gate.provider('VF5NP','BCM'))
        with self.assertRaises(ProviderNotReady):
            gate.verify_approved_profile('unregistered',lambda: b'SIMUL8!!',[])
        with self.assertRaises(ProviderNotReady): RealSeedKeyProvider(None,None,None)
        self.assertFalse(gate.validate(type('Fake',(),{'mock_only':False,'verified_real':True})(),
                                       'VF5NP','BCM','tx'))


class SubmissionCapabilityTests(unittest.TestCase):
    def setUp(self):
        from core.security_submission import SubmissionAuthority
        from tests.services.test_security_seed_request import seed_request
        self.now=10.0
        self.seed_request=seed_request()
        self.gate=ProviderVerificationGate(simulator=True)
        self.authority=SubmissionAuthority(self.gate.validate,clock=lambda:self.now)
        self.cancel=Event()
        self.material=self.gate.provider('BENCH','BCM').calculate(bytes(16),source_transaction=self.seed_request.transaction_id)

    def issue(self):
        return self.authority.issue(self.seed_request,self.material,connection_id='connection',
                                    epoch=1,authorization_id='grant',deadline=12,cancel=self.cancel)

    def test_manual_payload_stays_denied_and_generated_repr_is_redacted(self):
        from core.diagnostic_request import validate_send_policy,DiagnosticValidationError
        with self.assertRaises(DiagnosticValidationError): replace(self.seed_request,uds_payload=b'\x27\x02'+bytes(16))
        request=self.issue();validate_send_policy(request)
        self.assertEqual(len(request.uds_payload),18)
        self.assertNotIn(self.material.key.hex(),repr(request))
        self.assertNotIn(repr(self.material.key),repr(request))
        for values in (dict(ecu_name='EPS'),dict(tx_id=0x682),dict(generation=9),
                       dict(confirmed=False),dict(uds_payload=b'\x27\x02'+bytes(16))):
            with self.assertRaises(DiagnosticValidationError): replace(request,**values)

    def test_single_claim_expiry_replay_and_cancel(self):
        from core.diagnostic_request import DiagnosticValidationError
        request=self.issue()
        self.authority.claim(request,'connection',1,'grant',simulator=True)
        self.authority.check_active(request,'connection',1,'grant',simulator=True)
        with self.assertRaises(DiagnosticValidationError): self.authority.claim(request,'connection',1,'grant',simulator=True)
        self.authority.retire(request)
        with self.assertRaises(DiagnosticValidationError): self.authority.check_active(request,'connection',1,'grant',simulator=True)
        request=self.issue();self.now=12
        with self.assertRaises(DiagnosticValidationError): self.authority.claim(request,'connection',1,'grant',simulator=True)
        self.now=10;request=self.issue();self.cancel.set()
        with self.assertRaises(DiagnosticValidationError): self.authority.claim(request,'connection',1,'grant',simulator=True)

    def test_proof_never_crosses_owner_connection_session_or_bench(self):
        from core.security_submission import SubmissionAuthority
        from core.diagnostic_request import DiagnosticValidationError
        request=self.issue()
        for connection,epoch,grant,simulated in [('other',1,'grant',True),('connection',2,'grant',True),
                                               ('connection',1,'other',True),('connection',1,'grant',False)]:
            with self.assertRaises(DiagnosticValidationError): self.authority.claim(request,connection,epoch,grant,simulator=simulated)
        other=SubmissionAuthority(self.gate.validate,clock=lambda:self.now)
        with self.assertRaises(DiagnosticValidationError): other.claim(request,'connection',1,'grant',simulator=True)


class SecurityOwnerFlowTests(unittest.TestCase):
    def setUp(self):
        from services.can.simulated_backend import SimulatedCANBackend
        from services.can import CANService,CANConfig
        from core.bench_authorization import BenchAuthorizationContext
        from core.diagnostic_request import DiagnosticSettings
        self.backend=SimulatedCANBackend()
        self.service=CANService(self.backend)
        self.service.fn_connect(CANConfig('vector',0,500000,bench_context=BenchAuthorizationContext('sim-bench',True)))
        self.addCleanup(self.service.fn_disconnect)
        self.settings=DiagnosticSettings(p2_s=.05,p2_star_s=.1,total_s=.5)

    def transact(self,request):
        import time
        from services.can.diagnostic_client import DiagnosticClient
        self.service.fn_begin_diagnostic(request)
        try:
            client=DiagnosticClient(request,self.service.fn_send_diagnostic_frame)
            while client.result is None:
                client.poll()
                frame=self.service.fn_receive_diagnostic_frame()
                if frame is not None: client.feed(frame)
                time.sleep(.001)
            self.service.fn_diagnostic_completed(client.result)
            return client.result
        finally:
            self.service.fn_end_diagnostic(request.transaction_id)

    def prepare(self):
        from tests.services.test_security_seed_request import seed_request
        from services.can.security_access_session import SecurityAccessSession
        request=seed_request(settings=self.settings)
        self.transact(replace(request,uds_payload=b'\x10\x03',expected=b'\x50\x03'))
        session=SecurityAccessSession()
        session.start(request,self.service.capture_session_id,1)
        session.receive(self.transact(request),self.service.capture_session_id,1)
        session.calculate_verified(self.service.security_provider('BENCH','BCM'),self.service.security_gate)
        submission=self.service.prepare_security_submission(session,request,1,confirmed=True)
        return session,submission

    def test_full_extended_seed_calculation_key_and_exact_unlock(self):
        from core.diagnostic_request import DiagnosticOutcome
        from services.can.security_access_session import SecurityAccessState
        session,submission=self.prepare()
        result=self.transact(submission)
        self.assertTrue(session.finish_submission(result))
        self.assertEqual(result.outcome,DiagnosticOutcome.PASSED)
        self.assertEqual(result.response_payload,b'\x67\x02')
        self.assertEqual(session.state,SecurityAccessState.UNLOCKED)
        self.assertEqual([p[:2] for p in self.backend.requests],[b'\x10\x03',b'\x27\x01',b'\x27\x02'])
        self.assertEqual(len(self.backend.requests[-1]),18)
        self.assertTrue(any(f.direction=='TX' and f.data[0]==0x30 for f in self.backend.frames))
        self.assertTrue(any(f.direction=='RX' and f.data[0]==0x30 for f in self.backend.frames))

    def test_terminal_nrcs_never_unlock_or_retry(self):
        from services.can.security_access_session import SecurityAccessState
        names = {0x24: 'request sequence error', 0x33: 'security access denied',
                 0x35: 'invalid key', 0x36: 'exceeded number of attempts',
                 0x37: 'required time delay not expired'}
        for nrc, name in names.items():
            self.backend.key_response=bytes((0x7F,0x27,nrc))
            session,submission=self.prepare();result=self.transact(submission)
            self.assertFalse(session.finish_submission(result))
            self.assertEqual(result.nrc,nrc)
            self.assertIn(name, result.detail.lower())
            self.assertEqual(session.state,SecurityAccessState.FAILED)
        self.assertEqual(sum(p[:2]==b'\x27\x02' for p in self.backend.requests),5)

    def test_pending_delayed_final_timeout_and_malformed_positives(self):
        from core.diagnostic_request import DiagnosticOutcome
        self.backend.pending_delay=.07
        session,submission=self.prepare();result=self.transact(submission)
        self.assertEqual(result.pending_count,1)
        self.assertTrue(session.finish_submission(result))
        self.backend.pending_delay=0
        for response in (None,b'\x67\x02\x00',b'\x67\x01',b'\x7F\x27\x78'):
            self.backend.key_response=response
            session,submission=self.prepare();result=self.transact(submission)
            self.assertFalse(session.finish_submission(result))
            self.assertNotEqual(result.outcome,DiagnosticOutcome.PASSED)

    def test_one_shot_and_bench_revocation(self):
        from core.diagnostic_request import DiagnosticValidationError,DiagnosticCancelled
        session,submission=self.prepare()
        self.transact(submission)
        with self.assertRaises(DiagnosticValidationError): self.service.fn_begin_diagnostic(submission)
        session,submission=self.prepare()
        self.service.fn_begin_diagnostic(submission)
        self.service.fn_revoke_trusted_bench()
        try:
            with self.assertRaises(DiagnosticCancelled): self.service.fn_receive_diagnostic_frame()
        finally:
            self.service.fn_end_diagnostic(submission.transaction_id)

    def test_confirmed_extended_session_cannot_authorize_another_ecu(self):
        from core.diagnostic_request import DiagnosticValidationError
        from tests.services.test_security_seed_request import seed_request
        from services.can.security_access_session import SecurityAccessSession
        self.prepare()  # Extended session confirmed for BCM only.
        # A second ECU name on the same simulated bus must not inherit BCM's session.
        other = seed_request(ecu_name='EPS', settings=self.settings)
        session = SecurityAccessSession()
        session.start(other, self.service.capture_session_id, 1)
        session.receive(self.transact(other), self.service.capture_session_id, 1)
        session.calculate_verified(self.service.security_provider('BENCH', 'EPS'), self.service.security_gate)
        with self.assertRaises(DiagnosticValidationError):
            self.service.prepare_security_submission(session, other, 1, confirmed=True)
        self.assertFalse(any(p[:2] == b'\x27\x02' for p in self.backend.requests))
