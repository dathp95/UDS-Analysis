import unittest

from core.build_transactions import (
    build_transactions_v4,
    find_matching_positive_response,
    get_final_response_payload,
)


ECU_INFO = {
    "BMS": {
        "request": 0x693,
        "response": 0x613,
    }
}


def msg(timestamp, can_id, payload):
    return {
        "timestamp": timestamp,
        "can_id": can_id,
        "payload": payload,
    }


class TransactionMatchingTests(unittest.TestCase):
    def test_did_mismatch_does_not_match_positive_response(self):
        request = msg(957.621248, 0x693, "22 F0 70")
        positives = [
            msg(957.809713, 0x613, "62 F1 03 42 41 54 37 02 37 00 41 41")
        ]

        self.assertIsNone(
            find_matching_positive_response(
                request,
                positives,
                0x613,
                timeout=10.0,
            )
        )

    def test_eol_negative_response_is_final_for_22_f0_70(self):
        requests = [
            msg(957.621248, 0x693, "22 F0 70"),
            msg(957.792870, 0x693, "22 F1 03"),
        ]
        negatives = [
            msg(957.629702, 0x613, "7F 22 31"),
        ]
        positives = [
            msg(957.809713, 0x613, "62 F1 03 42 41 54 37 02 37 00 41 41"),
        ]

        transactions = build_transactions_v4(
            requests,
            positives,
            negatives,
            ECU_INFO,
            timeout=10.0,
        )

        first = transactions[0]
        self.assertEqual(first["status"], "NRC_ONLY")
        self.assertIsNone(first["positive_response"])
        self.assertEqual(get_final_response_payload(first), "7F 22 31")

        second = transactions[1]
        self.assertEqual(second["status"], "OK")
        self.assertEqual(
            get_final_response_payload(second),
            "62 F1 03 42 41 54 37 02 37 00 41 41",
        )

    def test_negative_response_must_match_request_sid(self):
        requests = [
            msg(1.0, 0x693, "22 F1 90"),
            msg(1.1, 0x693, "14 FF FF FF"),
        ]
        negatives = [
            msg(1.2, 0x613, "7F 14 31"),
        ]

        transactions = build_transactions_v4(
            requests,
            positive_responses=[],
            negative_responses=negatives,
            ecu_info=ECU_INFO,
            timeout=10.0,
        )

        self.assertEqual(transactions[0]["status"], "TIMEOUT")
        self.assertEqual(transactions[0]["negative_responses"], [])
        self.assertEqual(transactions[1]["status"], "NRC_ONLY")
        self.assertEqual(get_final_response_payload(transactions[1]), "7F 14 31")

    def test_positive_response_is_consumed_once(self):
        requests = [
            msg(1.0, 0x693, "22 F1 90"),
            msg(1.1, 0x693, "22 F1 90"),
        ]
        positives = [
            msg(1.2, 0x613, "62 F1 90 01"),
        ]

        transactions = build_transactions_v4(
            requests,
            positives,
            negative_responses=[],
            ecu_info=ECU_INFO,
            timeout=10.0,
        )

        ok_count = sum(tx["status"] == "OK" for tx in transactions)
        self.assertEqual(ok_count, 1)

    def test_response_pending_then_positive_is_ok(self):
        requests = [
            msg(1.0, 0x693, "22 F1 90"),
        ]
        negatives = [
            msg(1.1, 0x613, "7F 22 78"),
        ]
        positives = [
            msg(1.2, 0x613, "62 F1 90 01"),
        ]

        transactions = build_transactions_v4(
            requests,
            positives,
            negatives,
            ECU_INFO,
            timeout=10.0,
        )

        self.assertEqual(transactions[0]["status"], "OK")
        self.assertEqual(transactions[0]["response_pending_count"], 1)
        self.assertEqual(get_final_response_payload(transactions[0]), "62 F1 90 01")



    def test_ecu_reset_matches_reset_type(self):
        request = msg(1.0, 0x693, "11 01")
        positives = [
            msg(1.1, 0x613, "51 03"),
        ]

        self.assertIsNone(
            find_matching_positive_response(
                request,
                positives,
                0x613,
                timeout=10.0,
            )
        )

    def test_io_control_matches_did_not_only_first_did_byte(self):
        request = msg(1.0, 0x693, "2F F1 90 03")
        positives = [
            msg(1.1, 0x613, "6F F1 03 03"),
        ]

        self.assertIsNone(
            find_matching_positive_response(
                request,
                positives,
                0x613,
                timeout=10.0,
            )
        )
if __name__ == "__main__":
    unittest.main()
