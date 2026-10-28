"""Read-only provider eligibility. No ABI is approved in this release."""
from dataclasses import dataclass
from enum import Enum
import hashlib
from pathlib import Path

from core.dll_resource import DllResourceStatus, MAX_DLL_BYTES


class ProviderReadiness(Enum):
    MISSING = 'missing_dll'
    INVALID = 'invalid_dll'
    ARCH_UNSUPPORTED = 'unsupported_architecture'
    EXPORT_UNAVAILABLE = 'export_unavailable'
    DLL_MISMATCH = 'dll_mismatch'
    ABI_UNVERIFIED = 'abi_unverified'


@dataclass(frozen=True)
class SecurityProviderStatus:
    readiness: ProviderReadiness
    sha256: str = ''
    size_bytes: int = 0

    @property
    def live_enabled(self):
        # No settings/env flag can substitute for a reviewed ABI + real-vector proof.
        return False


def inspect_security_provider(vehicle_service, vehicle, ecu, *, expected_sha256=None):
    """Reuse saved Vehicle Manager resolution; never resolve/load a second DLL path."""
    metadata = vehicle_service.resolve_ecu_dll_resource(vehicle, ecu)
    if metadata.status in (DllResourceStatus.MISSING, DllResourceStatus.NOT_CONFIGURED):
        return SecurityProviderStatus(ProviderReadiness.MISSING)
    if not metadata.configurable:
        return SecurityProviderStatus(ProviderReadiness.INVALID)
    if metadata.machine != 'x86' or metadata.bits != 32:
        return SecurityProviderStatus(ProviderReadiness.ARCH_UNSUPPORTED)
    if not metadata.has_generate_key_ex:
        return SecurityProviderStatus(ProviderReadiness.EXPORT_UNAVAILABLE)
    try:
        digest = hashlib.sha256()
        size = 0
        with Path(metadata.path).open('rb') as stream:
            while part := stream.read(65536):
                size += len(part)
                if size > MAX_DLL_BYTES:
                    raise ValueError
                digest.update(part)
        if not size:
            raise ValueError
    except (OSError, ValueError):
        return SecurityProviderStatus(ProviderReadiness.INVALID)
    sha256 = digest.hexdigest()
    if expected_sha256 is not None and expected_sha256 != sha256:
        return SecurityProviderStatus(ProviderReadiness.DLL_MISMATCH, sha256, size)
    return SecurityProviderStatus(ProviderReadiness.ABI_UNVERIFIED, sha256, size)
