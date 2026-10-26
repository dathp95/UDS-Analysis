import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tests.dll_fixture import pe_dll


class DllResourceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path.cwd());self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def inspect(self,value,**kwargs):
        from core.dll_resource import inspect_dll_resource
        return inspect_dll_resource(value,base_dir=self.root,process_bits=64,**kwargs)

    def test_static_metadata_x64_x86_and_no_loader_execution(self):
        from core.dll_resource import DllResourceStatus as Status
        for machine,status in ((0x8664,Status.METADATA_AVAILABLE),(0x14C,Status.ARCH_UNSUPPORTED)):
            path=self.root/f'fake-{machine}.dll';path.write_bytes(pe_dll(machine))
            with patch('ctypes.CDLL',side_effect=AssertionError('No DLL execution')),patch('ctypes.WinDLL',side_effect=AssertionError('No DLL execution')):
                result=self.inspect(str(path))
            self.assertEqual(result.status,status)
            self.assertTrue(result.has_generate_key_ex)
            self.assertIn('GenerateKeyEx',result.exports)
            self.assertTrue(result.configurable)
            self.assertNotIn(str(self.root),repr(result))

    def test_missing_corrupt_extension_relative_and_unconfigured(self):
        from core.dll_resource import DllResourceStatus as Status
        self.assertEqual(self.inspect('').status,Status.NOT_CONFIGURED)
        self.assertEqual(self.inspect('missing.dll').status,Status.MISSING)
        path=self.root/'bad.dll';path.write_bytes(b'not a PE')
        self.assertEqual(self.inspect(str(path)).status,Status.MALFORMED)
        self.assertEqual(self.inspect(str(self.root)).status,Status.INVALID_FILE)
        path=self.root/'wrong.txt';path.write_bytes(pe_dll())
        self.assertEqual(self.inspect(str(path)).status,Status.INVALID_FILE)
        path=self.root/'relative.dll';path.write_bytes(pe_dll(export=b'OtherFunction'))
        result=self.inspect('relative.dll')
        self.assertEqual(result.path,str(path))
        self.assertEqual(result.status,Status.METADATA_AVAILABLE)
        self.assertFalse(result.has_generate_key_ex)
        self.assertIn('not exported',result.message)

    def test_unsafe_path_and_malformed_exports_have_friendly_status(self):
        from core.dll_resource import DllResourceStatus as Status
        for value in ('bad\0.dll','line\nbreak.dll',r'\\server\share\x.dll','https://host/x.dll'):
            self.assertEqual(self.inspect(value).status,Status.INVALID_PATH)
        data=bytearray(pe_dll());data[0x218:0x21C]=(0xFFFFFFFF).to_bytes(4,'little')
        path=self.root/'hostile.dll';path.write_bytes(data)
        self.assertEqual(self.inspect(str(path)).status,Status.MALFORMED)

    def test_immutable_metadata_unreadable_and_truncated_pe(self):
        from dataclasses import FrozenInstanceError
        from core.dll_resource import DllResourceStatus as Status
        result=self.inspect('')
        with self.assertRaises(FrozenInstanceError): result.path='changed'
        path=self.root/'fixture.dll';data=pe_dll();path.write_bytes(data)
        with patch.object(Path,'open',side_effect=PermissionError):
            self.assertEqual(self.inspect(str(path)).status,Status.INVALID_FILE)
        for length in (64,128,255):
            path.write_bytes(data[:length])
            self.assertEqual(self.inspect(str(path)).status,Status.MALFORMED)

    def test_bounded_malformed_export_tables(self):
        from core.dll_resource import DllResourceStatus as Status
        # Deterministically corrupt PE offsets and named-export table pointers.
        for offset in (0x3C,0x214,0x218,0x21C,0x220,0x224):
            data=bytearray(pe_dll());data[offset:offset+4]=b'\xff'*4
            path=self.root/'mutated.dll';path.write_bytes(data)
            self.assertEqual(self.inspect(str(path)).status,Status.MALFORMED,offset)
