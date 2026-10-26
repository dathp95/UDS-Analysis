import unittest
from threading import Thread
from unittest.mock import Mock
from core.diagnostic_request import DiagnosticRequest
from services.can import CANService, CANConfig, CANConnectionError
from tests.services.test_can_service import FakeCANBackend


class DiagnosticIoTests(unittest.TestCase):
    def test_connection_lease_serializes_and_guards_io(self):
        backend=FakeCANBackend()
        backend.fn_send_frame=Mock()
        backend.fn_receive_frame=Mock(return_value=None)
        service=CANService(backend)
        req=DiagnosticRequest('tx','row',1,'TEST','BCM',0x681,0x601,b'\x22\xf1\x90')
        with self.assertRaises(CANConnectionError): service.fn_begin_diagnostic(req)
        service.fn_connect(CANConfig('vector',0,500000))
        service.fn_begin_diagnostic(req)
        with self.assertRaises(CANConnectionError): service.fn_disconnect()
        failures=[]
        def other_thread():
            try: service.fn_receive_diagnostic_frame()
            except CANConnectionError as error: failures.append(error)
        thread=Thread(target=other_thread);thread.start();thread.join()
        self.assertEqual(len(failures),1)
        with self.assertRaises(CANConnectionError): service.fn_send_diagnostic_frame(0x682,b'\x01')
        service.fn_send_diagnostic_frame(0x681,b'\x03\x22\xf1\x90')
        service.fn_end_diagnostic(req.transaction_id)
        service.fn_disconnect()
        self.assertFalse(service.fn_is_connected())
