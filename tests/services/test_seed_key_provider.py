import json
import unittest
from dataclasses import replace
from threading import Event
from unittest.mock import patch


class SeedKeyProviderTests(unittest.TestCase):
    def request(self, **options):
        from services.seed_key_provider import SeedKeyRequest
        return SeedKeyRequest('request-1','VF5NP','BCM',1,b'PRIVATE_SEED',16,**options)

    def test_deterministic_mock_correlation_and_redaction(self):
        from services.seed_key_provider import MockSeedKeyProvider
        request=self.request()
        provider=MockSeedKeyProvider()
        with self.assertNoLogs(),patch('ctypes.CDLL',side_effect=AssertionError('No native loader')), \
                patch('ctypes.WinDLL',side_effect=AssertionError('No native loader')):
            first=provider.calculate(request)
        self.assertEqual(first,provider.calculate(request))
        self.assertEqual(first.request_id,request.request_id)
        self.assertEqual(len(first.key),16)
        self.assertNotIn('PRIVATE_SEED',repr(request))
        self.assertNotIn(first.key.hex(),repr(first))
        self.assertTrue(first.mock_only)

    def test_timeout_cancellation_and_crash_are_explicit_failures(self):
        from services.seed_key_provider import MockSeedKeyProvider,ProviderError,ProviderErrorCode
        for options,code in ((dict(delay_s=.03),ProviderErrorCode.TIMEOUT),
                             (dict(crash=True),ProviderErrorCode.WORKER_CRASH)):
            with self.assertRaises(ProviderError) as caught:
                MockSeedKeyProvider(**options).calculate(self.request(timeout_s=.005))
            self.assertEqual(caught.exception.code,code)
            self.assertNotIn('PRIVATE_SEED',str(caught.exception))
        cancel=Event();cancel.set()
        with self.assertRaises(ProviderError) as caught:
            MockSeedKeyProvider().calculate(self.request(),cancel=cancel)
        self.assertEqual(caught.exception.code,ProviderErrorCode.CANCELLED)

    def test_input_and_output_bounds_and_correlated_response_validation(self):
        from services.seed_key_provider import MockSeedKeyProvider,ProviderError,encode_request,decode_response
        request=self.request()
        for options in (dict(seed=b'x'*65),dict(output_size=65),dict(level=True),
                        dict(timeout_s=0),dict(timeout_s=float('nan')),dict(request_id='bad\nID'),dict(vehicle='bad\x7f')):
            with self.assertRaises(ProviderError):
                MockSeedKeyProvider().calculate(replace(request,**options))
        wire=encode_request(request)
        self.assertLessEqual(len(wire),4096)
        response=dict(version=1,request_id='wrong',status='ok',key_hex='00'*16,mock_only=True)
        with self.assertRaises(ProviderError): decode_response(json.dumps(response).encode(),request)
        response['request_id']=request.request_id
        for update in (dict(key_hex='FF'*65),dict(mock_only=False),dict(version=2),dict(status='native_ok')):
            with self.assertRaises(ProviderError):
                decode_response(json.dumps(dict(response,**update)).encode(),request)
        with self.assertRaises(ProviderError): decode_response(b'X'*4097,request)
        with self.assertRaises(ProviderError):
            decode_response(b'{"request_id":"wrong","request_id":"request-1"}',request)

    def test_inflight_cancellation_and_worker_error_envelope(self):
        from threading import Timer
        from services.seed_key_provider import MockSeedKeyProvider,ProviderError,ProviderErrorCode,decode_response
        event=Event();timer=Timer(.01,event.set);timer.start()
        try:
            with self.assertRaises(ProviderError) as caught:
                MockSeedKeyProvider(delay_s=.2).calculate(self.request(),cancel=event)
            self.assertEqual(caught.exception.code,ProviderErrorCode.CANCELLED)
        finally:
            timer.join()
        response=dict(version=1,request_id='request-1',status='error',error_code='worker_crash',mock_only=True)
        with self.assertRaises(ProviderError) as caught:
            decode_response(json.dumps(response).encode(),self.request())
        self.assertEqual(caught.exception.code,ProviderErrorCode.WORKER_CRASH)
