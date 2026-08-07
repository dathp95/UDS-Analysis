import unittest

from models.ecu import ECU
from models.vehicle import Vehicle
from services.vehicle_service import VehicleService


class FakeVehicleRepository:
    def __init__(self, vehicle):
        self.vehicle = vehicle
        self.saved_ecu = None

    def load(self, vehicle_name):
        if vehicle_name != self.vehicle.name:
            raise FileNotFoundError(vehicle_name)
        return self.vehicle

    def save_ecu(self, vehicle_name, ecu):
        self.saved_ecu = ecu


class VehicleServiceSaveTests(unittest.TestCase):
    def test_saves_renamed_ecu_with_same_request_and_response_ids(self):
        vehicle = Vehicle(
            name="VF3",
            ecus=[
                ECU(name="BCM", request_id="681", response_id="601"),
                ECU(name="ACM", request_id="688", response_id="608"),
            ],
        )
        repository = FakeVehicleRepository(vehicle)
        service = VehicleService()
        service._repository = repository

        service.save_ecu(
            "VF3",
            ECU(name="BCM_NEW", request_id="681", response_id="601"),
            existing_ecu_name="BCM",
        )

        self.assertEqual(repository.saved_ecu.name, "BCM_NEW")

    def test_rejects_renamed_ecu_when_new_name_already_exists(self):
        vehicle = Vehicle(
            name="VF3",
            ecus=[
                ECU(name="BCM", request_id="681", response_id="601"),
                ECU(name="ACM", request_id="688", response_id="608"),
            ],
        )
        service = VehicleService()
        service._repository = FakeVehicleRepository(vehicle)

        with self.assertRaisesRegex(ValueError, "ECU 'ACM' already exists"):
            service.save_ecu(
                "VF3",
                ECU(name="ACM", request_id="681", response_id="601"),
                existing_ecu_name="BCM",
            )

    def test_rejects_renamed_ecu_when_request_id_conflicts_with_other_ecu(self):
        vehicle = Vehicle(
            name="VF3",
            ecus=[
                ECU(name="BCM", request_id="681", response_id="601"),
                ECU(name="ACM", request_id="688", response_id="608"),
            ],
        )
        service = VehicleService()
        service._repository = FakeVehicleRepository(vehicle)

        with self.assertRaisesRegex(ValueError, "Duplicate Request ID"):
            service.save_ecu(
                "VF3",
                ECU(name="BCM_NEW", request_id="688", response_id="601"),
                existing_ecu_name="BCM",
            )


if __name__ == "__main__":
    unittest.main()