import os
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from models.ecu import ECU
from models.vehicle import Vehicle
from services.vehicle_service import VehicleService
from tests.dll_fixture import pe_dll


class VehicleDllStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source' / 'BCM.dll'
        self.source.parent.mkdir()
        self.source.write_bytes(pe_dll(0x14C))
        self.service = self.new_service(self.root / 'app')
        for name in ('VF5NP', 'VF6'):
            self.service.create_vehicle(Vehicle(name))
            self.service.add_ecu(name, ECU('BCM', '681', '601', resources={'dbc': 'keep', 'custom': 'keep'}))

    def new_service(self, app):
        service = VehicleService()
        service._repository.root = app / 'config' / 'vehicles'
        return service

    def save(self, vehicle='VF5NP', source=None):
        ecu = self.service.load_vehicle(vehicle).ecus[0]
        self.service.save_ecu(vehicle, ecu, dll_source=str(source or self.source))
        return self.service.load_vehicle(vehicle).ecus[0]

    def test_portable_per_vehicle_import_and_move_without_source_or_cwd(self):
        first = self.save()
        self.assertEqual(first.resources['dll'], 'resources/dll/BCM/BCM.dll')
        self.save('VF6')
        before = self.service.resolve_ecu_dll_resource('VF6', 'BCM')
        self.assertNotEqual(before.path, self.service.resolve_ecu_dll_resource('VF5NP', 'BCM').path)
        self.source.write_bytes(pe_dll(export=b'Different'))
        changed = self.save()
        self.assertNotEqual(first.resources['dll'], changed.resources['dll'])
        self.assertEqual(Path(before.path).read_bytes(), pe_dll(0x14C))
        self.assertEqual(changed.resources['custom'], 'keep')
        self.assertEqual(changed.resources['dbc'], 'keep')
        self.assertEqual((changed.request_id, changed.response_id), ('681', '601'))
        moved = self.root / 'moved'
        shutil.copytree(self.root / 'app', moved)
        self.source.unlink()
        self.source.parent.rmdir()
        old_cwd = Path.cwd()
        os.chdir(self.root)
        try:
            restarted = self.new_service(moved)
            for name in ('VF5NP', 'VF6'):
                metadata = restarted.resolve_ecu_dll_resource(name, 'BCM')
                self.assertTrue(metadata.configurable)
                self.assertTrue(Path(metadata.path).is_relative_to(moved))
        finally:
            os.chdir(old_cwd)

    def test_failed_copy_checksum_or_json_retains_old_reference_and_bytes(self):
        previous = self.save()
        path = Path(self.service.resolve_ecu_dll_resource('VF5NP', 'BCM').path)
        data = path.read_bytes()
        self.source.write_bytes(pe_dll(export=b'Changed'))
        from repositories import vehicle_dll_storage as storage
        for name in ('copy_stream', 'sha256_file', 'publish_file'):
            with patch.object(storage, name, side_effect=OSError('injected failure')):
                with self.assertRaises(ValueError): self.save()
            self.assertEqual(self.service.load_vehicle('VF5NP').ecus[0], previous)
            self.assertEqual(path.read_bytes(), data)
            self.assertEqual(list(path.parent.glob('*.tmp')), [])
        repository = self.service._repository
        real_write = repository._write_json
        def fail_vehicle_json(target, value):
            if target.name == 'vehicle.json': raise OSError('disk full')
            return real_write(target, value)
        with patch.object(repository, '_write_json', side_effect=fail_vehicle_json):
            with self.assertRaises(ValueError): self.save()
        self.assertEqual(self.service.load_vehicle('VF5NP').ecus[0], previous)
        self.assertEqual(list(path.parent.glob('*.dll')), [path])
        self.assertEqual(path.read_bytes(), data)

    def test_conflict_rename_and_delete_lifecycle(self):
        ecu = self.save()
        original_path = Path(self.service.resolve_ecu_dll_resource('VF5NP', 'BCM').path)
        self.service.save_ecu('VF5NP', replace(ecu, name='EPS'), existing_ecu_name='BCM')
        renamed = self.service.resolve_ecu_dll_resource('VF5NP', 'EPS')
        self.assertTrue(renamed.configurable)
        self.assertIn('/EPS/', Path(renamed.path).as_posix())
        self.service.delete_ecu('VF5NP', 'BCM')
        self.assertFalse(original_path.exists())
        self.service.delete_ecu('VF5NP', 'EPS')
        self.assertFalse(Path(renamed.path).exists())
        self.assertEqual(self.service.load_vehicle('VF5NP').ecus, [])

    def test_absolute_and_legacy_relative_paths_keep_their_meaning(self):
        ecu = self.service.load_vehicle('VF5NP').ecus[0]
        legacy = replace(ecu, resources={'dll': str(self.source)})
        self.service.save_ecu('VF5NP', legacy)
        self.assertEqual(self.service.resolve_ecu_dll_resource('VF5NP', 'BCM').path, str(self.source))
        relative = self.source.relative_to(Path.cwd()).as_posix()
        self.service._repository.save_ecu('VF5NP', replace(ecu, resources={'dll': relative}))
        self.assertEqual(self.service.resolve_ecu_dll_resource('VF5NP', 'BCM').path, str(self.source))
        self.assertFalse((self.service._repository.root / 'VF5NP' / 'resources').exists())

    def test_unsafe_paths_and_invalid_files_do_not_create_configuration(self):
        from core.vehicle_dll_paths import resolve_dll_path
        for value in ('resources/dll/BCM/../../outside.dll', r'C:relative.dll',
                      r'\\server\x.dll', 'resources/dll/EPS/BCM.dll'):
            with self.assertRaises(ValueError):
                resolve_dll_path(self.service._repository.root, 'VF5NP', 'BCM', value, path_base='vehicle')
        for data in (b'bad PE', b'X' * (16*1024*1024+1)):
            self.source.write_bytes(data)
            with self.assertRaises(ValueError): self.save()
        self.assertNotIn('dll', self.service.load_vehicle('VF5NP').ecus[0].resources)

    def test_checksum_mismatch_copied_pe_failure_and_version_conflict(self):
        from repositories import vehicle_dll_storage as storage
        ecu=self.save();old=Path(self.service.resolve_ecu_dll_resource('VF5NP','BCM').path)
        self.source.write_bytes(pe_dll(export=b'New'))
        digest=storage.sha256_file(self.source)
        with patch.object(storage,'sha256_file',side_effect=[digest,'0'*64]):
            with self.assertRaisesRegex(ValueError,'SHA-256'): self.save()
        real_inspect=storage.inspect_dll_resource
        from core.dll_resource import DllResourceMetadata,DllResourceStatus
        with patch.object(storage,'inspect_dll_resource',side_effect=[real_inspect(str(self.source)),
                  DllResourceMetadata(DllResourceStatus.MALFORMED,'bad copy')]):
            with self.assertRaisesRegex(ValueError,'Copied DLL'): self.save()
        version=old.with_name(f'BCM-{digest[:16]}.dll');version.write_bytes(b'user content')
        with self.assertRaisesRegex(ValueError,'conflict'): self.save()
        self.assertEqual(version.read_bytes(),b'user content')
        self.assertEqual(self.service.load_vehicle('VF5NP').ecus[0],ecu)
        self.assertEqual(list(old.parent.glob('.import-*')),[])

    def test_incomplete_rollback_keeps_new_copy_recovery_and_blocks_retry(self):
        from repositories import vehicle_dll_storage as storage
        self.save()
        repo=self.service._repository
        json_path=repo.root/'VF5NP/ecus/BCM.json';old_json=json_path.read_bytes()
        self.source.write_bytes(pe_dll(export=b'Updated'))
        real_atomic=storage.atomic_bytes
        real_writer=repo._write_json
        def deny_restore(path,data):
            if path==json_path and data==old_json: raise PermissionError('locked')
            return real_atomic(path,data)
        def fail_index(path,data):
            if path.name=='vehicle.json': raise OSError('index failure')
            return real_writer(path,data)
        with patch.object(storage,'atomic_bytes',side_effect=deny_restore),patch.object(repo,'_write_json',side_effect=fail_index):
            with self.assertRaisesRegex(storage.RollbackIncomplete,'rollback incomplete'): self.save()
        self.assertTrue(Path(self.service.resolve_ecu_dll_resource('VF5NP','BCM').path).exists())
        self.assertEqual(json_path.with_suffix('.json.recovery').read_bytes(),old_json)
        self.assertTrue((repo.root/'VF5NP/.dll-import.lock').exists())
        with self.assertRaisesRegex(ValueError,'lock'): self.save()

    def test_identical_save_clear_and_shared_legacy_reference_cleanup(self):
        first=self.save();path=Path(self.service.resolve_ecu_dll_resource('VF5NP','BCM').path)
        self.assertEqual(first,self.save())
        other=self.service.load_vehicle('VF6').ecus[0]
        self.service._repository.save_ecu('VF6',replace(other,resources={'dll':str(path)}))
        self.service.save_ecu('VF5NP',replace(first,resources={'dll':''}))
        self.assertTrue(path.exists())  # A legacy absolute reference still uses this copy.
        self.assertTrue(self.service.resolve_ecu_dll_resource('VF6','BCM').configurable)
        with self.assertRaisesRegex(ValueError,'referenced by another Vehicle'):
            self.service.delete_vehicle('VF5NP')
        self.assertTrue(path.exists())
        self.service.save_ecu('VF6',replace(other,resources={'dll':''}))
        self.service.delete_vehicle('VF5NP')
        self.assertFalse((self.service._repository.root/'VF5NP').exists())
        self.assertTrue((self.service._repository.root/'VF6').exists())

    def test_symlink_escape_is_rejected_without_touching_target(self):
        from core.vehicle_dll_paths import resolve_dll_path
        root=self.service._repository.root/'VF5NP'
        outside=self.root/'outside';outside.mkdir();(outside/'BCM.dll').write_bytes(pe_dll())
        link=root/'resources';
        try:
            link.symlink_to(outside,target_is_directory=True)
        except OSError:
            # Windows may deny symlink creation without Developer Mode. The same guard
            # is exercised deterministically when physical creation is unavailable.
            original=Path.is_symlink
            with patch.object(Path,'is_symlink',lambda path: path==link or original(path)):
                with self.assertRaises(ValueError): resolve_dll_path(self.service._repository.root,'VF5NP','BCM','resources/dll/BCM/BCM.dll',path_base='vehicle')
                with self.assertRaises(ValueError): self.save()
        else:
            with self.assertRaises(ValueError): resolve_dll_path(self.service._repository.root,'VF5NP','BCM','resources/dll/BCM/BCM.dll',path_base='vehicle')
            with self.assertRaises(ValueError): self.save()
        self.assertEqual((outside/'BCM.dll').read_bytes(),pe_dll())
        self.assertNotIn('dll',self.service.load_vehicle('VF5NP').ecus[0].resources)

    def test_case_only_rename_is_rejected_before_any_disk_change(self):
        ecu=self.save()
        folder=self.service._repository.root/'VF5NP'
        before={p.relative_to(folder).as_posix():p.read_bytes() for p in folder.rglob('*') if p.is_file()}
        with self.assertRaisesRegex(ValueError,'Case-only'):
            self.service.save_ecu('VF5NP',replace(ecu,name='bcm'),existing_ecu_name='BCM')
        self.assertEqual(before,{p.relative_to(folder).as_posix():p.read_bytes() for p in folder.rglob('*') if p.is_file()})

    def test_global_writer_lock_covers_reference_scan_and_cleanup(self):
        first=self.save()
        repo=self.service._repository
        old=repo.root/'VF5NP'/first.resources['dll']
        self.source.write_bytes(pe_dll(export=b'Changed'))
        real_collect=repo._collect_dll
        attempts=[]
        def competing_save(vehicle,ecu):
            # A second repository/service cannot reselect the old copy mid-cleanup.
            second=self.new_service(self.root/'app')
            with self.assertRaisesRegex(ValueError,'locked'):
                second.save_ecu('VF5NP',first)
            attempts.append(True)
            real_collect(vehicle,ecu)
        with patch.object(repo,'_collect_dll',side_effect=competing_save):
            self.save()
        self.assertEqual(attempts,[True])
        self.assertFalse(old.exists())
        self.assertFalse((repo.root/'.vehicle-resources.lock').exists())

    def test_stale_portable_draft_cannot_replace_current_valid_reference(self):
        stale=self.save()
        self.source.write_bytes(pe_dll(export=b'Newer'))
        current=self.save()
        second=self.new_service(self.root/'app')
        with self.assertRaisesRegex(ValueError,'DLL'):
            second._repository.save_ecu('VF5NP',stale)
        self.assertEqual(self.service.load_vehicle('VF5NP').ecus[0],current)
        self.assertTrue(self.service.resolve_ecu_dll_resource('VF5NP','BCM').configurable)

    def test_legacy_relative_reserved_prefix_is_not_reinterpreted(self):
        from core.vehicle_dll_paths import resolve_dll_path
        legacy_root=self.root/'legacy-app'
        legacy=legacy_root/'resources/dll/BCM/BCM.dll';legacy.parent.mkdir(parents=True)
        legacy.write_bytes(pe_dll())
        result=resolve_dll_path(self.service._repository.root,'VF5NP','BCM',
                                'resources/dll/BCM/BCM.dll',project_root=legacy_root)
        self.assertEqual(result,legacy)

    def test_rename_json_failure_restores_old_definition_and_managed_copy(self):
        ecu=self.save();repo=self.service._repository
        old_json=repo.root/'VF5NP/ecus/BCM.json';before=old_json.read_bytes()
        original=Path.unlink
        def locked_old_json(path,*args,**kwargs):
            if path==old_json: raise PermissionError('locked old ECU')
            return original(path,*args,**kwargs)
        with patch.object(Path,'unlink',locked_old_json):
            with self.assertRaises(ValueError):
                self.service.save_ecu('VF5NP',replace(ecu,name='EPS'),existing_ecu_name='BCM')
        self.assertEqual(old_json.read_bytes(),before)
        self.assertEqual([value.name for value in self.service.load_vehicle('VF5NP').ecus],['BCM'])
        self.assertTrue(self.service.resolve_ecu_dll_resource('VF5NP','BCM').configurable)
        self.assertFalse((repo.root/'VF5NP/ecus/EPS.json').exists())
        self.assertEqual(list((repo.root/'VF5NP/resources/dll/EPS').glob('*.dll')),[])
