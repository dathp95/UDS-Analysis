from models.vehicle import Vehicle
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