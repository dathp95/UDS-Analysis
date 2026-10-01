import unittest

from core.transaction_formatter import fn_build_transaction_rows


EXPECTED_KEYS = [
    "ECU",
    "Time",
    "Activity",
    "Request",
    "Response",
    "RT (ms)",
    "Status",
]


class TransactionFormatterTests(unittest.TestCase):

    def test_build_transaction_rows_uses_positive_response_and_rounds_rt_ms(self):
        transactions = [
            {
                "ecu": "BCM",
                "display_name": "Read VIN",
                "request": {
                    "timestamp": 1.25,
                    "payload": "22 F1 90",
                },
                "positive_response": {
                    "payload": "62 F1 90",
                },
                "negative_responses": [
                    {"payload": "7F 22 78"},
                ],
                "response_time": 0.012345,
                "status": "OK",
            }
        ]

        rows = fn_build_transaction_rows(transactions)

        self.assertEqual(
            rows,
            [
                {
                    "ECU": "BCM",
                    "Time": 1.25,
                    "Activity": "Read VIN",
                    "Request": "22 F1 90",
                    "Response": "62 F1 90",
                    "RT (ms)": 12.35,
                    "Status": "OK",
                }
            ],
        )
        self.assertEqual(list(rows[0].keys()), EXPECTED_KEYS)

    def test_build_transaction_rows_uses_empty_values_for_missing_optional_data(self):
        transactions = [
            {
                "ecu": "BCM",
                "display_name": "Read VIN",
                "negative_responses": [],
                "response_time": None,
                "status": "TIMEOUT",
            }
        ]

        rows = fn_build_transaction_rows(transactions)

        self.assertEqual(
            rows[0],
            {
                "ECU": "BCM",
                "Time": "",
                "Activity": "Read VIN",
                "Request": "",
                "Response": "",
                "RT (ms)": "",
                "Status": "TIMEOUT",
            },
        )
        self.assertEqual(list(rows[0].keys()), EXPECTED_KEYS)

    def test_build_transaction_rows_uses_last_negative_response_without_positive(self):
        transactions = [
            {
                "ecu": "BCM",
                "display_name": "Read VIN",
                "request": {
                    "timestamp": 1.25,
                    "payload": "22 F1 90",
                },
                "positive_response": None,
                "negative_responses": [
                    {"payload": "7F 22 31"},
                    {"payload": "7F 22 78"},
                ],
                "response_time": None,
                "status": "NRC_ONLY",
            }
        ]

        rows = fn_build_transaction_rows(transactions)

        self.assertEqual(rows[0]["Response"], "7F 22 78")
        self.assertEqual(rows[0]["RT (ms)"], "")
        self.assertEqual(list(rows[0].keys()), EXPECTED_KEYS)


if __name__ == "__main__":
    unittest.main()
