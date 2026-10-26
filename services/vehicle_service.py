from models.vehicle import Vehicle
from models.ecu import ECU
from repositories.vehicle_repository import VehicleRepository


class VehicleService:
    """
    Service layer for Vehicle Packages.

    Coordinates business logic between the GUI
    and the VehicleRepository.
    """

    def __init__(self):

        self._repository = VehicleRepository()

    def list_vehicles(self) -> list[str]:
        """
        Return all available vehicle packages.
        """

        return self._repository.list_vehicles()

    def load_vehicle(
        self,
        vehicle_name: str,
    ) -> Vehicle:
        """
        Load a complete vehicle package.
        """

        return self._repository.load(
            vehicle_name
        )

    def create_vehicle(
        self,
        vehicle: Vehicle,
    ) -> None:

        self._validate_vehicle(vehicle)

        self._repository.create_vehicle(
            vehicle
        )

    def resolve_ecu_dll_resource(self, vehicle_name, ecu_name):
        """Return immutable static metadata; never load or execute a configured DLL."""
        from services.ecu_dll_resource import resolve_ecu_dll_resource
        return resolve_ecu_dll_resource(self,vehicle_name,ecu_name)

    def delete_vehicle(
        self,
        vehicle_name: str,
    ) -> None:

        vehicle_name = vehicle_name.strip()

        if not vehicle_name:

            raise ValueError(
                "Vehicle name cannot be empty."
            )

        self._repository.delete_vehicle(
            vehicle_name
        )

    def export_vehicle_ecu_list(
        self,
        vehicle_name: str,
    ) -> str:

        vehicle_name = vehicle_name.strip()

        if not vehicle_name:

            raise ValueError(
                "Vehicle name cannot be empty."
            )

        vehicle = self._repository.load(
            vehicle_name
        )

        return "\n".join(
            "|".join(
                (
                    ecu.name,
                    ecu.request_id,
                    ecu.response_id,
                )
            )
            for ecu in vehicle.ecus
        )

    def save_ecu(
        self,
        vehicle_name: str,
        ecu: ECU,
        existing_ecu_name: str = "",
        *,
        dll_source: str | None = None,
    ) -> bool:
        """Save ECU; True means an imported-resource rename removed the old definition."""

        vehicle = self._repository.load(vehicle_name)

        self._validate_ecu(
            vehicle=vehicle,
            ecu=ecu,
            existing_ecu_name=existing_ecu_name or ecu.name,
        )

        previous = next((item for item in vehicle.ecus if item.name == (existing_ecu_name or ecu.name)),None)
        old_dll = (previous.resources or {}).get('dll','') if previous else ''
        new_dll = (ecu.resources or {}).get('dll','')
        if previous and previous.name != ecu.name and previous.name.casefold() == ecu.name.casefold():
            raise ValueError('Case-only ECU rename is unsupported; use a distinct ECU name.')
        if dll_source is None and previous and previous.name != ecu.name:
            from core.vehicle_dll_paths import is_managed_dll, resolve_dll_path
            if is_managed_dll(previous.resources) and new_dll == old_dll:
                dll_source = str(resolve_dll_path(self._repository.root, vehicle_name, previous.name, old_dll, path_base='vehicle'))
        if dll_source is not None:
            try:
                return self._repository.import_ecu_dll(vehicle_name, ecu, dll_source,
                                                       existing_ecu_name=existing_ecu_name)
            except OSError:
                raise ValueError('DLL import or configuration Save failed. Previous configuration was retained unless recovery was explicitly reported.') from None
        new_base = (ecu.resources or {}).get('dll_path_base','project')
        old_base = (previous.resources or {}).get('dll_path_base','project') if previous else 'project'
        if (new_dll != old_dll or new_base != old_base) and new_dll:
            from core.dll_resource import inspect_dll_resource
            from core.vehicle_dll_paths import resolve_dll_path
            metadata = inspect_dll_resource(str(resolve_dll_path(self._repository.root, vehicle_name, ecu.name, new_dll, path_base=new_base)))
            if not metadata.configurable: raise ValueError(metadata.message)

        try:
            self._repository.save_ecu(vehicle_name, ecu)
        except OSError:
            raise ValueError('ECU Save failed; previous configuration retained unless recovery was explicitly reported.') from None
        return False

    def add_ecu(
        self,
        vehicle_name: str,
        ecu: ECU,
    ) -> None:

        vehicle = self._repository.load(vehicle_name)

        self._validate_ecu(
            vehicle=vehicle,
            ecu=ecu,
            existing_ecu_name="",
        )

        self._repository.add_ecu(
            vehicle_name,
            ecu,
        )

    def delete_ecu(
        self,
        vehicle_name: str,
        ecu_name: str,
    ) -> None:

        self._repository.delete_ecu(
            vehicle_name,
            ecu_name,
        )

    # ==========================================
    # Validation
    # ==========================================

    def _validate_vehicle(
        self,
        vehicle: Vehicle,
    ) -> None:

        vehicle.name = vehicle.name.strip()

        if not vehicle.name:

            raise ValueError(
                "Vehicle name cannot be empty."
            )

        invalid_chars = set('\\/:*?"<>|')

        if any(char in invalid_chars for char in vehicle.name):

            raise ValueError(
                "Vehicle name contains invalid characters."
            )

        for existing_name in self._repository.list_vehicles():

            if existing_name.lower() == vehicle.name.lower():

                raise ValueError(
                    f"Vehicle '{vehicle.name}' already exists."
                )

    def _validate_ecu(
        self,
        vehicle: Vehicle,
        ecu: ECU,
        existing_ecu_name: str = "",
    ) -> None:

        ecu.name = ecu.name.strip()

        if not ecu.name:

            raise ValueError(
                "ECU name cannot be empty."
            )

        existing_ecu_name = existing_ecu_name.strip().lower()

        for existing in vehicle.ecus:

            existing_name = existing.name.lower()

            if existing_name == existing_ecu_name:

                continue

            if existing_name == ecu.name.lower():

                raise ValueError(
                    f"ECU '{ecu.name}' already exists."
                )

            self._validate_duplicate_id(
                field_name="Request ID",
                new_value=ecu.request_id,
                existing_value=existing.request_id,
            )

            self._validate_duplicate_id(
                field_name="Response ID",
                new_value=ecu.response_id,
                existing_value=existing.response_id,
            )

    @staticmethod
    def _validate_duplicate_id(
        field_name: str,
        new_value: str,
        existing_value: str,
    ) -> None:

        new_value = (new_value or "").strip().lower()

        existing_value = (existing_value or "").strip().lower()

        if not new_value:

            return

        if new_value == existing_value:

            raise ValueError(
                f"Duplicate {field_name}: {new_value.upper()}."
            )
