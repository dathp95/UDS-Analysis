import re
from uuid import uuid4

from core.diagnostic_request import DiagnosticRequest, DiagnosticSettings, DiagnosticValidationError as Invalid
from repositories.diagnostic_sequence_repository import DiagnosticSequenceRepository
from services.ecu_configuration import resolve_vehicle_ecu


def parse_can_id(value):
    if not isinstance(value,str) or not re.fullmatch(r'(?:0[xX])?[0-9A-Fa-f]{1,8}',value.strip()):
        raise Invalid('ECU CAN IDs must be hexadecimal strings.')
    result=int(value.strip(),16)
    if result > 0x7FF:
        raise Invalid('29-bit ECU addressing is not supported in M04.')
    return result


def resolve_request(vehicle_service, vehicle_name, step, step_id, generation, settings=None):
    try:
        vehicle,ecu=resolve_vehicle_ecu(vehicle_service,vehicle_name,step.ecu)
    except ValueError as error:
        raise Invalid(str(error)) from error
    tx_id,rx_id=parse_can_id(ecu.request_id),parse_can_id(ecu.response_id)
    for other in vehicle.ecus:
        if other is ecu: continue
        for field,value in (('request_id',tx_id),('response_id',rx_id)):
            try: candidate=parse_can_id(getattr(other,field))
            except Invalid: continue
            if candidate == value:
                raise Invalid('ECU CAN IDs are shared by multiple configured ECUs.')
    try:
        payload=bytes.fromhex(DiagnosticSequenceRepository._normalize_hex(step.request,'request'))
        expected=bytes.fromhex(DiagnosticSequenceRepository._normalize_hex(step.expected_response,'expected',allow_empty=True))
    except ValueError as error:
        raise Invalid(str(error)) from error
    return DiagnosticRequest(uuid4().hex,step_id,generation,vehicle_name,ecu.name,tx_id,rx_id,payload,expected,step.match,
                             settings if settings is not None else DiagnosticSettings())
