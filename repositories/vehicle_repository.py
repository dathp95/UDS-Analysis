import json
import shutil

from config.paths import VEHICLES_DIR

from models.vehicle import Vehicle
from models.ecu import ECU


class VehicleRepository:
    """
    Repository for managing Vehicle Packages.

    Responsible for reading/writing vehicle configuration
    from the filesystem.
    """

    def __init__(self):

        self.root = VEHICLES_DIR

    # ==========================================
    # Paths
    # ==========================================

    def _vehicle_dir(
        self,
        vehicle_name: str,
    ):

        return self.root / vehicle_name

    def _vehicle_file(
        self,
        vehicle_name: str,
    ):

        return self._vehicle_dir(vehicle_name) / "vehicle.json"

    def _ecu_dir(
        self,
        vehicle_name: str,
    ):

        return self._vehicle_dir(vehicle_name) / "ecus"

    def _ecu_file(
        self,
        vehicle_name: str,
        ecu_name: str,
    ):

        return self._ecu_dir(vehicle_name) / f"{ecu_name}.json"

    def list_vehicles(self) -> list[str]:
        """
        Return all available vehicle package names.

        Example:
            ["VF3", "VF5", "VF6"]
        """

        if not self.root.exists():
            return []

        vehicles = []

        for item in self.root.iterdir():

            if item.is_dir():

                vehicles.append(item.name)

        vehicles.sort()

        return vehicles


    def _load_vehicle_json(
            self,
            vehicle_name: str,
        ) -> dict:
        """
        Load vehicle.json from a Vehicle Package.

        Returns
        -------
        dict
            Parsed vehicle configuration.
        """

        vehicle_file = self._vehicle_file(vehicle_name)

        if not vehicle_file.exists():

            raise FileNotFoundError(
                f"Vehicle package not found: {vehicle_file}"
            )

        with open(
            vehicle_file,
            "r",
            encoding="utf-8-sig",
        ) as file:

            return json.load(file)

    def _load_ecu_json(
            self,
            vehicle_name: str,
            ecu_name: str,
        ) -> dict:
        """
        Load one ECU configuration.

        Returns
        -------
        dict
        """

        ecu_file = self._ecu_file(vehicle_name, ecu_name)

        if not ecu_file.exists():

            raise FileNotFoundError(
                f"ECU configuration not found: {ecu_file}"
            )

        with open(
            ecu_file,
            "r",
            encoding="utf-8-sig",
        ) as file:

            return json.load(file)

    @staticmethod
    def _to_vehicle(data: dict) -> Vehicle:
        """
        Convert a dictionary into a Vehicle object.

        Notes
        -----
        ECU objects are loaded separately.
        """

        return Vehicle(
            name=data["name"],
            manufacturer=data.get(
                "manufacturer",
                "",
            ),
            version=data.get(
                "version",
                "1.0.0",
            ),
            description=data.get(
                "description",
                "",
            ),
        )


    @staticmethod
    def _to_ecu(data: dict) -> ECU:
        """
        Convert a dictionary into an ECU object.
        """

        return ECU(

            name=data["name"],

            request_id=data.get(
                "request_id",
                "",
            ),

            response_id=data.get(
                "response_id",
                "",
            ),

            aliases=data.get(
                "aliases",
                [],
            ),

            resources=data.get(
                "resources",
                {},
            ),

            quick_requests=data.get(
                "quick_requests",
                [],
            ),
        )   

    @staticmethod
    def _ecu_to_json(ecu: ECU) -> dict:

        return {
            "name": ecu.name,
            "request_id": ecu.request_id,
            "response_id": ecu.response_id,
            "aliases": ecu.aliases,
            "resources": ecu.resources,
            "quick_requests": ecu.quick_requests,
        }

    @staticmethod
    def _vehicle_to_json(vehicle: Vehicle) -> dict:

        return {
            "name": vehicle.name,
            "manufacturer": vehicle.manufacturer,
            "version": vehicle.version,
            "description": vehicle.description,
            "ecus": [
                ecu.name
                for ecu in vehicle.ecus
            ],
        }

    @staticmethod
    def _write_json(
        path,
        data: dict,
    ) -> None:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False,
            )


    def create_vehicle(
        self,
        vehicle: Vehicle,
    ) -> None:

        vehicle_dir = self._vehicle_dir(vehicle.name)

        if vehicle_dir.exists():

            raise FileExistsError(
                f"Vehicle package already exists: {vehicle.name}"
            )

        self._write_json(
            self._vehicle_file(vehicle.name),
            self._vehicle_to_json(vehicle),
        )

        self._ecu_dir(vehicle.name).mkdir(
            parents=True,
            exist_ok=True,
        )

    def delete_vehicle(
        self,
        vehicle_name: str,
    ) -> None:

        vehicle_dir = self._vehicle_dir(vehicle_name)

        if not vehicle_dir.exists():

            raise FileNotFoundError(
                f"Vehicle package not found: {vehicle_name}"
            )

        shutil.rmtree(vehicle_dir)


    def load(
            self,
            vehicle_name: str,
        ) -> Vehicle:
        """
        Load a complete Vehicle Package.

        Parameters
        ----------
        vehicle_name
            Vehicle package name.

        Returns
        -------
        Vehicle
            Fully loaded vehicle object.
        """

        vehicle_data = self._load_vehicle_json(
            vehicle_name
        )

        vehicle = self._to_vehicle(
            vehicle_data
        )

        for ecu_name in vehicle_data.get(
            "ecus",
            [],
        ):

            ecu_data = self._load_ecu_json(
                vehicle_name,
                ecu_name,
            )

            ecu = self._to_ecu(
                ecu_data
            )

            vehicle.ecus.append(
                ecu
            )

        return vehicle

    def save_ecu(
            self,
            vehicle_name: str,
            ecu: ECU,
        ) -> None:

        vehicle_data = self._load_vehicle_json(vehicle_name)

        ecu_names = vehicle_data.get(
            "ecus",
            [],
        )

        if ecu.name not in ecu_names:

            ecu_names.append(ecu.name)

        vehicle_data["ecus"] = ecu_names

        self._write_json(
            self._vehicle_file(vehicle_name),
            vehicle_data,
        )

        self._write_json(
            self._ecu_file(vehicle_name, ecu.name),
            self._ecu_to_json(ecu),
        )

    def add_ecu(
        self,
        vehicle_name: str,
        ecu: ECU,
    ) -> None:

        vehicle_data = self._load_vehicle_json(vehicle_name)

        ecu_names = vehicle_data.get(
            "ecus",
            [],
        )

        if ecu.name not in ecu_names:

            ecu_names.append(ecu.name)

        vehicle_data["ecus"] = ecu_names

        self._write_json(
            self._vehicle_file(vehicle_name),
            vehicle_data,
        )

        self._write_json(
            self._ecu_file(vehicle_name, ecu.name),
            self._ecu_to_json(ecu),
        )

    def delete_ecu(
        self,
        vehicle_name: str,
        ecu_name: str,
    ) -> None:

        vehicle_data = self._load_vehicle_json(vehicle_name)

        vehicle_data["ecus"] = [
            item
            for item in vehicle_data.get(
                "ecus",
                [],
            )
            if item != ecu_name
        ]

        self._write_json(
            self._vehicle_file(vehicle_name),
            vehicle_data,
        )

        ecu_file = self._ecu_file(
            vehicle_name,
            ecu_name,
        )

        if ecu_file.exists():

            ecu_file.unlink()
