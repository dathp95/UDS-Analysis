import json
import shutil

from config.paths import VEHICLES_DIR

from models.vehicle import Vehicle
from models.ecu import ECU
from core.dll_resource import inspect_dll_resource
from core.vehicle_dll_paths import contained_path, is_managed_dll, resolve_dll_path, safe_component, vehicle_directory
from repositories.vehicle_dll_storage import ResourceCleanupError, atomic_json, commit_json, import_dll, serialized_resources


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

        atomic_json(path, data)


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

    @serialized_resources
    def delete_vehicle(
        self,
        vehicle_name: str,
    ) -> None:

        vehicle_dir = vehicle_directory(self.root, vehicle_name)

        for name in self.list_vehicles():
            if name == vehicle_name:
                continue
            for ecu in self.load(name).ecus:
                for key, value in (ecu.resources or {}).items():
                    if not isinstance(value, str) or not value:
                        continue
                    try:
                        base = (ecu.resources or {}).get('dll_path_base','project') if key == 'dll' else 'project'
                        path = resolve_dll_path(self.root, name, ecu.name, value, path_base=base).resolve()
                    except (ValueError, OSError):
                        continue
                    if path.is_relative_to(vehicle_dir):
                        raise ValueError('Vehicle resources are referenced by another Vehicle; update those references before deleting.')

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

    @serialized_resources
    def save_ecu(self, vehicle_name: str, ecu: ECU) -> None:
        self._save_ecu_data(vehicle_name, ecu)

    def _save_ecu_data(
            self,
            vehicle_name: str,
            ecu: ECU,
            *,
            collect_resources=True,
            existing_ecu_name="",
        ) -> None:

        vehicle_data = self._load_vehicle_json(vehicle_name)
        if any(name != ecu.name and name.casefold() == ecu.name.casefold() for name in vehicle_data.get('ecus', [])):
            raise ValueError('Case-only ECU rename is unsupported; use a distinct ECU name.')
        previous_path = self._ecu_file(vehicle_name, ecu.name)
        previous = self._to_ecu(self._load_ecu_json(vehicle_name, ecu.name)) if previous_path.exists() else None
        reference = (ecu.resources or {}).get('dll', '')
        old_reference = (previous.resources or {}).get('dll', '') if previous else ''
        # Validate changed managed references inside the writer lock. A stale draft
        # must not restore a collected file and then collect the current valid copy.
        previous_base = (previous.resources or {}).get('dll_path_base','project') if previous else 'project'
        if is_managed_dll(ecu.resources) and (reference != old_reference or previous_base != 'vehicle'):
            path = resolve_dll_path(self.root, vehicle_name, ecu.name, reference, path_base='vehicle')
            if not inspect_dll_resource(str(path)).configurable:
                raise ValueError('DLL reference is missing or invalid; reload the ECU before saving this draft.')

        ecu_names = vehicle_data.get(
            "ecus",
            [],
        )

        if ecu.name not in ecu_names:

            ecu_names.append(ecu.name)
        renamed = existing_ecu_name and existing_ecu_name != ecu.name
        if renamed:
            ecu_names = [name for name in ecu_names if name != existing_ecu_name]

        vehicle_data["ecus"] = ecu_names

        updates = {self._ecu_file(vehicle_name, ecu.name): self._ecu_to_json(ecu),
                   self._vehicle_file(vehicle_name): vehicle_data}
        if renamed:
            updates[self._ecu_file(vehicle_name, existing_ecu_name)] = None
        commit_json(updates, self._write_json)
        if collect_resources and previous:
            self._collect_dll(vehicle_name, previous)

    @serialized_resources
    def import_ecu_dll(self, vehicle_name, ecu, source, *, existing_ecu_name=""):
        root = vehicle_directory(self.root, vehicle_name)
        contained_path(root, 'vehicle.json')
        contained_path(root, 'ecus', safe_component(ecu.name) + '.json')
        if existing_ecu_name:
            contained_path(root, 'ecus', safe_component(existing_ecu_name) + '.json')
        previous = self.load(vehicle_name)
        old = next((item for item in previous.ecus if item.name == (existing_ecu_name or ecu.name)), None)
        with import_dll(self.root, vehicle_name, ecu, source) as imported:
            self._save_ecu_data(vehicle_name, imported, collect_resources=False,
                                existing_ecu_name=existing_ecu_name)
        if old:
            self._collect_dll(vehicle_name, old)
        return bool(old and old.name != ecu.name)

    def _collect_dll(self, vehicle_name, old_ecu):
        reference = (old_ecu.resources or {}).get('dll', '')
        if not is_managed_dll(old_ecu.resources):
            return
        try:
            old_path = resolve_dll_path(self.root, vehicle_name, old_ecu.name, reference, path_base='vehicle')
            for name in self.list_vehicles():
                for ecu in self.load(name).ecus:
                    for key, value in (ecu.resources or {}).items():
                        if not isinstance(value, str) or not value:
                            continue
                        if name == vehicle_name and value.replace('\\', '/').casefold() == reference.casefold():
                            return
                        try:
                            base = (ecu.resources or {}).get('dll_path_base','project') if key == 'dll' else 'project'
                            if resolve_dll_path(self.root, name, ecu.name, value, path_base=base).resolve() == old_path:
                                return
                        except (OSError, ValueError):
                            continue
            old_path.unlink(missing_ok=True)
            # Remove only empty managed directories; never recursively delete a computed path.
            parent = old_path.parent
            vehicle_root = vehicle_directory(self.root, vehicle_name)
            while parent != vehicle_root:
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent
        except (OSError, ValueError):
            raise ResourceCleanupError('Configuration saved, but a previous managed DLL could not be cleaned up. Review its Vehicle resource directory.') from None

    @serialized_resources
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

    @serialized_resources
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

        ecu_file = self._ecu_file(
            vehicle_name,
            ecu_name,
        )

        old_ecu = self._to_ecu(self._load_ecu_json(vehicle_name, ecu_name)) if ecu_file.exists() else None
        commit_json({self._vehicle_file(vehicle_name): vehicle_data, ecu_file: None}, self._write_json)
        if old_ecu:
            self._collect_dll(vehicle_name, old_ecu)
