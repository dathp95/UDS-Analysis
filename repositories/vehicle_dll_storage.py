"""Portable DLL import and JSON publication helpers. No native DLL loading."""
from contextlib import contextmanager
from dataclasses import replace
from functools import wraps
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from core.dll_resource import MAX_DLL_BYTES, inspect_dll_resource
from core.vehicle_dll_paths import contained_path, safe_component, vehicle_directory


class RollbackIncomplete(ValueError):
    pass


class ResourceCleanupError(ValueError):
    """Configuration committed successfully, but an obsolete managed file remains."""


@contextmanager
def resource_lock(root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    lock = root / '.vehicle-resources.lock'
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError('Vehicle resources are locked by another Save/Delete or an interrupted transaction. Review recovery state before retrying.') from None
    os.close(descriptor)
    retain = False
    try:
        yield
    except RollbackIncomplete:
        retain = True
        raise
    finally:
        if not retain:
            lock.unlink(missing_ok=True)


def serialized_resources(operation):
    @wraps(operation)
    def guarded(repository, *args, **kwargs):
        with resource_lock(repository.root):
            return operation(repository, *args, **kwargs)
    return guarded


def atomic_bytes(path, data):
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def atomic_json(path, value):
    atomic_bytes(path, (json.dumps(value, indent=4, ensure_ascii=False) + '\n').encode('utf-8'))


def commit_json(updates, writer):
    """Rollback handled failures; publication order always leaves resolvable DLL references."""
    originals = {path: path.read_bytes() if path.exists() else None for path in updates}
    changed = []
    try:
        for path, value in updates.items():
            changed.append(path)
            if value is None:
                path.unlink(missing_ok=True)
            else:
                writer(path, value)
    except Exception:
        failures = []
        for path in reversed(changed):
            try:
                if originals[path] is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_bytes(path, originals[path])
            except OSError:
                failures.append(path)
                # Retain an explicit recovery snapshot if the destination is locked.
                if originals[path] is not None:
                    try:
                        atomic_bytes(path.with_suffix(path.suffix + '.recovery'), originals[path])
                    except OSError:
                        pass  # Still report incomplete rollback and retain all DLL copies.
        if failures:
            raise RollbackIncomplete('Save failed; rollback incomplete. DLL copies retained. Review JSON and any .recovery snapshots before retrying.') from None
        raise


def sha256_file(path):
    digest = hashlib.sha256()
    count = 0
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(64*1024), b''):
            count += len(block)
            if count > MAX_DLL_BYTES:
                raise ValueError('DLL exceeds the static inspection size limit.')
            digest.update(block)
    return digest.hexdigest()


def copy_stream(source, destination):
    digest = hashlib.sha256()
    count = 0
    with Path(source).open('rb') as reader, Path(destination).open('wb') as writer:
        for block in iter(lambda: reader.read(64*1024), b''):
            count += len(block)
            if count > MAX_DLL_BYTES:
                raise ValueError('DLL changed or exceeds the import size limit.')
            digest.update(block)
            writer.write(block)
        writer.flush()
        os.fsync(writer.fileno())
    return digest.hexdigest()


def publish_file(temporary, destination):
    # A cooperative per-Vehicle writer lock covers conflict selection and publication.
    if destination.exists():
        raise ValueError('DLL destination changed during import; retry Save.')
    os.replace(temporary, destination)


@contextmanager
def import_dll(repository_root, vehicle_name, ecu, source):
    vehicle_root = vehicle_directory(repository_root, vehicle_name)
    lock = vehicle_root / '.dll-import.lock'
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError('Another DLL Save is active, or a previous interrupted Save left a lock. Review the Vehicle folder before retrying.') from None
    os.close(descriptor)
    temporary = destination = None
    created = False
    retain_lock = False
    try:
        metadata = inspect_dll_resource(source)
        if not metadata.configurable:
            raise ValueError(metadata.message)
        source = Path(metadata.path)
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', source.name)
        safe_component(name)
        if len(name) > 128:
            raise ValueError('DLL filename is too long for portable storage.')
        destination_dir = contained_path(vehicle_root, 'resources', 'dll', safe_component(ecu.name))
        destination_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=destination_dir, suffix='.dll', prefix='.import-', delete=False) as stream:
            temporary = Path(stream.name)
        expected = sha256_file(source)
        copied = copy_stream(source, temporary)
        if copied != expected or sha256_file(temporary) != expected or sha256_file(source) != expected:
            raise ValueError('DLL SHA-256 verification failed; no configuration was saved.')
        if not inspect_dll_resource(str(temporary)).configurable:
            raise ValueError('Copied DLL failed static PE validation.')
        destination = destination_dir / name
        if destination.exists() and sha256_file(destination) != expected:
            destination = destination_dir / f'{Path(name).stem}-{expected[:16]}.dll'
        # Also rejects a pre-existing destination symlink/junction, even inside the root.
        destination = contained_path(vehicle_root, *destination.relative_to(vehicle_root).parts)
        if destination.exists():
            if sha256_file(destination) != expected:
                raise ValueError('Versioned DLL filename conflict; existing contents were retained.')
        else:
            publish_file(temporary, destination)
            created = True
        resources = dict(ecu.resources or {})
        resources['dll'] = destination.relative_to(vehicle_root).as_posix()
        resources['dll_path_base'] = 'vehicle'
        yield replace(ecu, resources=resources)
    except RollbackIncomplete:
        # JSON may already reference the new copy: never remove it in this state.
        retain_lock = True
        raise
    except Exception:
        if created:
            destination.unlink(missing_ok=True)
        raise
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if not retain_lock:
            lock.unlink(missing_ok=True)
