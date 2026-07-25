from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from repositories.vehicle_repository import VehicleRepository


def main():

    repo = VehicleRepository()

    print()

    print("=" * 50)
    print("Complete Vehicle")
    print("=" * 50)

    vehicle = repo.load("VF3")

    print(vehicle)

    print()

    print("=" * 50)
    print("ECUs")
    print("=" * 50)

    for ecu in vehicle.ecus:

        print(
            ecu.name,
            ecu.request_id,
            ecu.response_id,
        )


if __name__ == "__main__":
    main()