import json
import os
import tempfile
from pathlib import Path

from config.paths import QUICK_FILTER_FILE

class QuickAccessService:

    def __init__(self):

        self.json_file = QUICK_FILTER_FILE

    def fn_load(self) -> list:
        """
        Load all quick filters.
        """

        if not self.json_file.exists():

            return []

        with open(
            self.json_file,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)
        
    def fn_save(
            self,
            filters,
        ) -> None:
        """
        Save all quick filters.
        """

        with open(
                self.json_file,
                "w",
                encoding="utf-8"
            ) as file:

            json.dump(

                filters,

                file,

                indent=4,

                ensure_ascii=False

            )
   
 

    def fn_reorder(self, filter_ids: list[int]) -> None:
        """Persist a complete ID permutation without changing filter contents."""
        filters = self.fn_load()
        if not isinstance(filters, list) or any(
            not isinstance(item, dict) or type(item.get("id")) is not int
            for item in filters
        ):
            raise ValueError("Stored quick filters must have integer IDs.")
        stored_ids = [item["id"] for item in filters]
        if (
            any(type(filter_id) is not int for filter_id in filter_ids)
            or len(set(stored_ids)) != len(stored_ids)
            or len(set(filter_ids)) != len(filter_ids)
            or set(filter_ids) != set(stored_ids)
        ):
            raise ValueError("Order must contain every stored filter ID exactly once.")

        by_id = {item["id"]: item for item in filters}
        destination = Path(self.json_file)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=destination.parent,
                prefix=f".{destination.name}.", suffix=".tmp", delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump([by_id[filter_id] for filter_id in filter_ids],
                          temporary, indent=4, ensure_ascii=False)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, destination)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def fn_add(
            self,
            quick_filter: dict,
        ) -> None:
        """
        Add one quick filter.
        """

        filters = self.fn_load()

        new_filter = {

            "id": self._fn_next_id(filters),

            "name": quick_filter["name"],

            "enabled": True,

            "filters": quick_filter["filters"]

        }

        filters.append(
            new_filter
        )

        self.fn_save(
            filters
        )

    def fn_add_many(self, quick_filters):
        filters = self.fn_load()
        for quick_filter in quick_filters:
            filters.append({
                "id": self._fn_next_id(filters),
                "name": quick_filter["name"],
                "enabled": True,
                "filters": quick_filter["filters"],
            })
        self.fn_save(filters)

    def fn_export_filters(self):
        filters = self.fn_load()

        return "\n".join(
            self._fn_format_filter(item)
            for item in filters
        )

    def fn_insert_after(self, source_id, quick_filter):
        filters = self.fn_load()
        new_filter = {
            "id": self._fn_next_id(filters),
            "name": quick_filter["name"],
            "enabled": True,
            "filters": quick_filter["filters"],
        }
        for index, item in enumerate(filters):
            if item.get("id") == source_id:
                filters.insert(index + 1, new_filter)
                self.fn_save(filters)
                return new_filter
        raise ValueError(f"Quick filter ID {source_id} not found.")
        

   
    
    def fn_update(
            self,
            quick_filter: dict,
        ):
        """
        Update one quick filter.
        """

        filters = self.fn_load()

        for index, item in enumerate(filters):

            if item["id"] == quick_filter["id"]:

                filters[index] = quick_filter

                self.fn_save(filters)

                return

        raise ValueError(
            f"Quick filter ID {quick_filter['id']} not found."
        )
    
    def fn_delete(
            self,
            quick_filter_id: int,
        ):
        """
        Delete one quick filter.
        """

        filters = self.fn_load()

        filters = [

            item

            for item in filters

            if item["id"] != quick_filter_id

        ]

        self.fn_save(
            filters
        )

    def _fn_next_id(
            self,
            filters: list,
        ):
        """
        Generate the next available ID.
        """

        if not filters:

            return 1

        return max(

            item["id"]

            for item in filters

        ) + 1

    @staticmethod
    def _fn_format_filter(quick_filter):
        filters = quick_filter.get("filters", {})

        return "|".join(
            (
                quick_filter.get("name", ""),
                filters.get("ecu", ""),
                filters.get("request", ""),
                filters.get("response", ""),
            )
        )
