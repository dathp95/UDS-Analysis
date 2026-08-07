from core.services.quick_access_service import (
    QuickAccessService
)

class QuickAccessController:

    def __init__(self):

        self.quick_access_service = QuickAccessService()
    
    def fn_load(self):
        """
        Load all quick filters.
        """

        return self.quick_access_service.fn_load()
    
    def fn_add(
            self,
            quick_filter: dict,
        ):
        """
        Add one quick filter.
        """

        self.quick_access_service.fn_add(
            quick_filter
        )

    def fn_add_many(self, quick_filters):
        return self.quick_access_service.fn_add_many(quick_filters)

    def fn_export_filters(self):
        return self.quick_access_service.fn_export_filters()

    def fn_insert_after(self, source_id, quick_filter):
        return self.quick_access_service.fn_insert_after(source_id, quick_filter)

    def fn_update(
            self,
            quick_filter: dict,
        ):
        """
        Update one quick filter.
        """

        self.quick_access_service.fn_update(
            quick_filter
        )
    
    def fn_delete(
            self,
            quick_filter_id: int,
        ):
        """
        Delete one quick filter.
        """

        self.quick_access_service.fn_delete(
            quick_filter_id
        )
