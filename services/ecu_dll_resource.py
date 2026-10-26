"""Read-only resolution; the saved ECU resources remain the only path store."""
from core.dll_resource import DllResourceMetadata,DllResourceStatus,inspect_dll_resource
from services.ecu_configuration import resolve_vehicle_ecu
from core.vehicle_dll_paths import resolve_dll_path
from config.paths import VEHICLES_DIR


def resolve_ecu_dll_resource(vehicle_service,vehicle_name: str,ecu_name: str) -> DllResourceMetadata:
    try:
        _,ecu=resolve_vehicle_ecu(vehicle_service,vehicle_name,ecu_name)
    except ValueError:
        return DllResourceMetadata(DllResourceStatus.CONFIGURATION_ERROR,'Select a valid Vehicle and unambiguous ECU.')
    resources=ecu.resources if isinstance(ecu.resources,dict) else {}
    reference=resources.get('dll','')
    if not reference:
        return inspect_dll_resource(reference)
    repository=getattr(vehicle_service,'_repository',None)
    root=getattr(repository,'root',VEHICLES_DIR)
    try:
        path=resolve_dll_path(root,vehicle_name,ecu_name,reference,
                              path_base=resources.get('dll_path_base','project'))
    except (ValueError, OSError, RuntimeError):
        return DllResourceMetadata(DllResourceStatus.INVALID_PATH,'Invalid or escaping DLL resource reference.')
    return inspect_dll_resource(str(path))
