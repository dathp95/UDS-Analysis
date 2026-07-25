from pathlib import Path

from config.paths import VEHICLES_DIR

import json

from pathlib import Path

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

        vehicle_file = (
            self.root
            / vehicle_name
            / "vehicle.json"
        )

        if not vehicle_file.exists():

            raise FileNotFoundError(
                f"Vehicle package not found: {vehicle_file}"
            )

        with open(
            vehicle_file,
            "r",
            encoding="utf-8",
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

        ecu_file = (
            self.root
            / vehicle_name
            / "ecus"
            / f"{ecu_name}.json"
        )

        if not ecu_file.exists():

            raise FileNotFoundError(
                f"ECU configuration not found: {ecu_file}"
            )

        with open(
            ecu_file,
            "r",
            encoding="utf-8",
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

            functional_id=data.get(
                "functional_id",
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