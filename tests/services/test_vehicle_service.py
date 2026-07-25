from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.vehicle_service import VehicleService


def main():

    service = VehicleService()

    print("=" * 50)
    print("Available Vehicles")
    print("=" * 50)

    vehicles = service.list_vehicles()

    print(vehicles)

    print()

    print("=" * 50)
    print("Load Vehicle")
    print("=" * 50)

    vehicle = service.load_vehicle("VF3")

    print(vehicle)

    print()

    print("=" * 50)
    print("ECU List")
    print("=" * 50)

    for ecu in vehicle.ecus:

        print(
            f"{ecu.name:<10}"
            f"Req: {ecu.request_id:<5}"
            f"Resp: {ecu.response_id}"
        )


if __name__ == "__main__":
    main()