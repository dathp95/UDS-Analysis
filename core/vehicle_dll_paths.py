"""Explicit DLL path bases; unmarked references retain legacy app-root semantics."""
from pathlib import Path, PureWindowsPath
from config.paths import PROJECT_ROOT


def safe_component(value: str) -> str:
    if (not isinstance(value, str) or not value or value in ('.', '..')
            or value.endswith((' ', '.')) or PureWindowsPath(value).is_reserved()
            or any(ord(c) < 32 or c in '\\/:*?"<>|' for c in value)):
        raise ValueError('Invalid Vehicle, ECU or DLL filename component.')
    return value


def contained_path(base, *parts) -> Path:
    try:
        base = Path(base).resolve()
        candidate = base.joinpath(*parts)
        resolved = candidate.resolve()
    except (OSError, RuntimeError):
        raise ValueError('DLL resource root is unreadable or contains invalid links.') from None
    if not resolved.is_relative_to(base):
        raise ValueError('DLL resource path escapes its configured root.')
    current = base
    for part in candidate.relative_to(base).parts:
        current /= part
        if current.is_symlink() or (hasattr(current, 'is_junction') and current.is_junction()):
            raise ValueError('Linked DLL resource directories are unsupported.')
    return resolved


def vehicle_directory(repository_root, vehicle_name: str) -> Path:
    return contained_path(repository_root, safe_component(vehicle_name))


def is_portable_reference(value) -> bool:
    return isinstance(value, str) and value.replace('\\', '/').startswith('resources/dll/')


def is_managed_dll(resources) -> bool:
    return bool(resources and resources.get('dll_path_base') == 'vehicle'
                and is_portable_reference(resources.get('dll')))


def resolve_dll_path(repository_root, vehicle_name: str, ecu_name: str, reference: str,
                     *, project_root=PROJECT_ROOT, path_base='project') -> Path:
    if not isinstance(reference, str) or not reference:
        raise ValueError('DLL reference is empty or invalid.')
    if path_base not in ('project', 'vehicle'):
        raise ValueError('Unknown DLL path base.')
    raw = reference.strip().strip('"')
    windows = PureWindowsPath(raw)
    if (any(ord(c) < 32 for c in raw) or raw.startswith('\\\\') or '://' in raw
            or '..' in windows.parts or windows.is_reserved()):
        raise ValueError('Unsafe DLL resource reference.')
    if windows.is_absolute():
        return Path(raw)  # Legacy explicit absolute reference; static inspector validates it.
    if windows.drive or windows.root:
        raise ValueError('Drive-relative and rooted DLL references are unsupported.')
    for part in windows.parts:
        safe_component(part)
    if path_base == 'vehicle':
        parts = windows.parts
        if not is_portable_reference(raw) or len(parts) != 4 or parts[2] != safe_component(ecu_name):
            raise ValueError('Portable DLL reference must belong to the selected ECU.')
        return contained_path(vehicle_directory(repository_root, vehicle_name), *parts)
    return contained_path(project_root, *windows.parts)
