import unittest

from models.ecu import ECU
from models.vehicle import Vehicle
from services.vehicle_service import VehicleService


class FakeVehicleRepository:
    def __init__(self, vehicle):
        self.vehicle = vehicle

    def load(self, vehicle_name):
        if vehicle_name != self.vehicle.name:
            raise FileNotFoundError(vehicle_name)
        return self.vehicle


class VehicleServiceExportTests(unittest.TestCase):
    def test_exports_vehicle_ecus_using_import_ecu_list_format(self):
        vehicle = Vehicle(
            name="VF3",
            ecus=[
                ECU(name="BCM", request_id="681", response_id="601"),
                ECU(name="ACM", request_id="688", response_id="608"),
            ],
        )
        service = VehicleService()
        service._repository = FakeVehicleRepository(vehicle)

        self.assertEqual(
            service.export_vehicle_ecu_list("VF3"),
            "BCM|681|601\nACM|688|608",
        )

    def test_rejects_empty_vehicle_name(self):
        service = VehicleService()

        with self.assertRaises(ValueError):
            service.export_vehicle_ecu_list(" ")


if __name__ == "__main__":
    unittest.main()
