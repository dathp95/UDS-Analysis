import unittest

from core.services.quick_access_service import QuickAccessService


class FakeQuickAccessService(QuickAccessService):
    def __init__(self, filters):
        self.filters = filters

    def fn_load(self):
        return self.filters


class QuickAccessExportTests(unittest.TestCase):
    def test_exports_filters_using_import_filter_format(self):
        service = FakeQuickAccessService(
            [
                {
                    "id": 1,
                    "name": "Read VIN MHU",
                    "enabled": True,
                    "filters": {
                        "ecu": "MHU",
                        "request": "22 F1 90",
                        "response": "62 F1 90",
                    },
                },
                {
                    "id": 2,
                    "name": "Write VIN BCM",
                    "enabled": True,
                    "filters": {
                        "ecu": "BCM",
                        "request": "2E F1 90",
                        "response": "6E F1 90",
                    },
                },
            ]
        )

        self.assertEqual(
            service.fn_export_filters(),
            "Read VIN MHU|MHU|22 F1 90|62 F1 90\n"
            "Write VIN BCM|BCM|2E F1 90|6E F1 90",
        )

    def test_exports_missing_filter_fields_as_empty_columns(self):
        service = FakeQuickAccessService(
            [
                {
                    "name": "ECU only",
                    "filters": {
                        "ecu": "BCM",
                    },
                },
            ]
        )

        self.assertEqual(
            service.fn_export_filters(),
            "ECU only|BCM||",
        )


if __name__ == "__main__":
    unittest.main()
