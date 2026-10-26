"""Canonical Vehicle/ECU selection shared by diagnostic and resource resolvers."""
def resolve_vehicle_ecu(vehicle_service,vehicle_name,ecu_name):
    if (not isinstance(vehicle_name,str) or not vehicle_name or vehicle_name in ('.','..')
            or any(char in vehicle_name for char in '\\/:\0')):
        raise ValueError('Select a valid Vehicle configuration.')
    try: vehicle=vehicle_service.load_vehicle(vehicle_name)
    except Exception as error: raise ValueError('Cannot load the selected Vehicle configuration.') from error
    if vehicle.name!=vehicle_name: raise ValueError('Selected Vehicle changed while resolving configuration.')
    matches=[ecu for ecu in vehicle.ecus if ecu.name==ecu_name]
    if len(matches)!=1: raise ValueError('ECU is missing or ambiguous in the selected Vehicle.')
    return vehicle,matches[0]
