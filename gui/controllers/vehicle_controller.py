from models.vehicle import Vehicle

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