import json
from zipfile import Path

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
   
    # def fn_add(
    #         self,
    #         quick_filter: dict,
    #     )-> None:
    #     """
    #     Add one quick filter.
    #     """

    #     filters = self.fn_load()

    #     new_filter = quick_filter.copy()
    #     new_filter["id"] = self._fn_next_id(filters)
    #     new_filter["enabled"] = True

    #     filters.append(new_filter)
        
    #     self.fn_save(
    #         filters
    #     )

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

                self.fn_save(
                    filters
                )

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