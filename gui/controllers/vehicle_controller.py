from models.vehicle import Vehicle
from models.ecu import ECU

from services.vehicle_service import VehicleService


class VehicleController:

    def __init__(self):

        self._service = VehicleService()

    # ==========================================
    # Public
    # ==========================================

    def list_vehicles(self) -> list[str]:
        """
        Return all available vehicle packages.
        """

        return self._service.list_vehicles()

    def load_vehicle(
        self,
        vehicle_name: str,
    ) -> Vehicle:
        """
        Load one vehicle package.
        """

        return self._service.load_vehicle(
            vehicle_name
        )

    def create_vehicle(
        self,
        vehicle: Vehicle,
    ) -> None:

        self._service.create_vehicle(
            vehicle
        )

    def delete_vehicle(
        self,
        vehicle_name: str,
    ) -> None:

        self._service.delete_vehicle(
            vehicle_name
        )

    def save_ecu(
        self,
        vehicle_name: str,
        ecu: ECU,
    ) -> None:

        self._service.save_ecu(
            vehicle_name,
            ecu,
        )

    def add_ecu(
        self,
        vehicle_name: str,
        ecu: ECU,
    ) -> None:

        self._service.add_ecu(
            vehicle_name,
            ecu,
        )

    def delete_ecu(
        self,
        vehicle_name: str,
        ecu_name: str,
    ) -> None:

        self._service.delete_ecu(
            vehicle_name,
            ecu_name,
        )
