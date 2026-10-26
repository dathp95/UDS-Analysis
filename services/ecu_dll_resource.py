"""Read-only resolution; the saved ECU resources remain the only path store."""
from core.dll_resource import DllResourceMetadata,DllResourceStatus,inspect_dll_resource
from services.ecu_configuration import resolve_vehicle_ecu


def resolve_ecu_dll_resource(vehicle_service,vehicle_name: str,ecu_name: str) -> DllResourceMetadata:
    try:
        _,ecu=resolve_vehicle_ecu(vehicle_service,vehicle_name,ecu_name)
    except ValueError:
        return DllResourceMetadata(DllResourceStatus.CONFIGURATION_ERROR,'Select a valid Vehicle and unambiguous ECU.')
    resources=ecu.resources if isinstance(ecu.resources,dict) else {}
    return inspect_dll_resource(resources.get('dll',''))
