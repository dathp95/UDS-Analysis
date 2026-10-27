from dataclasses import dataclass
from pathlib import Path

from services.ecu_configuration import resolve_vehicle_ecu
from core.vehicle_dll_paths import resolve_dll_path

from services.can.seed_key_dll_inspector import (
    DLLInformation,
    inspect_dll,
)


@dataclass(frozen=True)
class ECUSeedKeyConfiguration:
    vehicle: str
    ecu: str
    dll: DLLInformation


def inspect_ecu_seed_key_dll(
    vehicle_service,
    repository_root,
    vehicle_name: str,
    ecu_name: str,
) -> ECUSeedKeyConfiguration:

    vehicle, ecu = resolve_vehicle_ecu(
        vehicle_service,
        vehicle_name,
        ecu_name,
    )

    # Adapt the following property to the existing
    # ECU resource model if necessary.
    resources = getattr(ecu, "resources", None) or {}

    reference = resources.get("dll")

    if not reference:
        raise ValueError(
            f"No DLL configured for {ecu_name}."
        )

    path_base = resources.get(
        "dll_path_base",
        "project",
    )

    dll_path = resolve_dll_path(
        repository_root,
        vehicle.name,
        ecu.name,
        reference,
        path_base=path_base,
    )

    dll_info = inspect_dll(dll_path)

    return ECUSeedKeyConfiguration(
        vehicle=vehicle.name,
        ecu=ecu.name,
        dll=dll_info,
    )