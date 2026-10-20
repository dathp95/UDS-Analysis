import tempfile
import unittest
from pathlib import Path

import can
from openpyxl import load_workbook

from core.build_transactions import build_transactions_v4, get_final_response_payload
from core.pipeline import run_pipeline
from core.report_engine import build_ecu_reports, build_summary_report
from core.report_export import export_workbook
from core.transaction_formatter import fn_build_transaction_rows
from models.ecu import ECU
from models.vehicle import Vehicle
from tests.core.test_dsa_txt_parser import HEADER, dsa_frame
from tests.core.test_transaction_matching import msg


ECUS = {"A": {"request": 0x682, "response": 0x602},
        "B": {"request": 0x693, "response": 0x613}}


class ResponsePendingTests(unittest.TestCase):
    def match(self, positives=(), negatives=(), requests=None, **kwargs):
        return build_transactions_v4(
            requests or [msg(1, 0x682, "31 01 02 06")], list(positives),
            list(negatives), ECUS, timeout=1, **kwargs)

    def test_normal_positive(self):
        tx = self.match([msg(1.1, 0x602, "71 01 02 06 00")])[0]
        self.assertEqual(tx["status"], "OK")
        self.assertAlmostEqual(tx["response_time"], .1)

    def test_pending_extends_normal_timeout(self):
        tx = self.match([msg(12, 0x602, "71 01 02 06 00")],
                        [msg(1.1, 0x602, "7F 31 78")])[0]
        self.assertEqual(tx["status"], "OK")
        self.assertAlmostEqual(tx["response_time"], 11)
        self.assertEqual(tx["response_pending_count"], 1)

    def test_repeated_pending_preserves_details(self):
        negatives = [msg(t, 0x602, "7F 31 78") for t in (1.1, 4, 9)]
        tx = self.match([msg(12, 0x602, "71 01 02 06")], negatives)[0]
        self.assertEqual(tx["status"], "OK")
        self.assertEqual(tx["response_pending_count"], 3)
        self.assertEqual(tx["negative_responses"], negatives)

    def test_pending_only_has_no_final_response(self):
        tx = self.match(negatives=[msg(1.1, 0x602, "7F 31 78")])[0]
        self.assertEqual(tx["status"], "PENDING_TIMEOUT")
        self.assertEqual(get_final_response_payload(tx), "")
        self.assertIsNone(tx["response_time"])

    def test_terminal_negative_after_pending(self):
        tx = self.match(negatives=[msg(1.1, 0x602, "7F 31 78"),
                                   msg(12, 0x602, "7F 31 22")])[0]
        self.assertEqual(tx["status"], "NRC_ONLY")
        self.assertEqual(get_final_response_payload(tx), "7F 31 22")
        self.assertEqual(tx["response_time"], 11)

    def test_terminal_negative_stops_search_before_later_positive(self):
        tx = self.match([msg(1.5, 0x602, "71 01 02 06")],
                        [msg(1.1, 0x602, "7F 31 22")])[0]
        self.assertEqual(tx["status"], "NRC_ONLY")
        self.assertIsNone(tx["positive_response"])

    def test_other_ecu_request_does_not_interrupt_pending(self):
        txs = self.match([msg(12, 0x602, "71 01 02 06"),
                          msg(2.1, 0x613, "62 F1 90 00")],
                         [msg(1.1, 0x602, "7F 31 78")],
                         [msg(1, 0x682, "31 01 02 06"), msg(2, 0x693, "22 F1 90")])
        self.assertEqual([tx["status"] for tx in txs], ["OK", "OK"])

    def test_same_routine_retry_is_ambiguous_not_assigned_to_retry(self):
        txs = self.match([msg(3, 0x602, "71 01 02 06")],
                         [msg(1.1, 0x602, "7F 31 78"), msg(2.1, 0x602, "7F 31 78")],
                         [msg(1, 0x682, "31 01 02 06"), msg(2, 0x682, "31 01 02 06")])
        self.assertEqual([tx["status"] for tx in txs],
                         ["PENDING_AMBIGUOUS", "PENDING_AMBIGUOUS"])
        self.assertTrue(all(tx["positive_response"] is None for tx in txs))
        self.assertEqual(txs[0]["response_pending_count"], 1)

    def test_same_ecu_different_service_interrupts_pending_conservatively(self):
        txs = self.match([msg(3, 0x602, "71 01 02 06"), msg(2.1, 0x602, "50 03")],
                         [msg(1.1, 0x602, "7F 31 78")],
                         [msg(1, 0x682, "31 01 02 06"), msg(2, 0x682, "10 03")])
        self.assertEqual([tx["status"] for tx in txs], ["PENDING_AMBIGUOUS", "OK"])

    def test_tester_present_does_not_interrupt_pending(self):
        txs = self.match([msg(12, 0x602, "71 01 02 06")],
                         [msg(1.1, 0x602, "7F 31 78")],
                         [msg(1, 0x682, "31 01 02 06"), msg(2, 0x682, "3E 80")])
        self.assertEqual(txs[0]["status"], "OK")

    def test_wild_clear_diagnostic_terminal_negative_after_ten_seconds(self):
        tx = build_transactions_v4([msg(31.994685, 0x682, "14 FF FF FF")], [],
            [msg(t, 0x602, "7F 14 78") for t in
             (32.048895, 33.549796, 35.051266, 36.562835, 38.058473, 39.560158,
              41.061087, 42.562590)] + [msg(43.116299, 0x602, "7F 14 72")], ECUS, 10)[0]
        self.assertEqual(get_final_response_payload(tx), "7F 14 72")
        self.assertEqual(tx["response_pending_count"], 8)
        self.assertAlmostEqual(tx["response_time"], 11.121614)

    def test_explicit_timeout_boundaries_and_invalid_limits(self):
        tx = self.match([msg(6, 0x602, "71 01 02 06")],
                        [msg(2, 0x602, "7F 31 78")], pending_timeout=5)[0]
        self.assertEqual(tx["status"], "OK")
        for value in (0, -1, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.match(pending_timeout=value)

    def test_routine_id_subfunction_sid_and_response_id_must_match(self):
        positives = [msg(3, 0x613, "71 01 02 06"), msg(4, 0x602, "71 01 02 07"),
                     msg(5, 0x602, "71 03 02 06"), msg(6, 0x602, "62 01 02 06"),
                     msg(7, 0x602, "71 01 02 06")]
        tx = self.match(positives, [msg(1.1, 0x602, "7F 31 78")])[0]
        self.assertEqual(tx["positive_response"], positives[-1])

    def test_pending_timeout_is_total_bounded_not_restarted(self):
        tx = self.match([msg(7, 0x602, "71 01 02 06")],
                        [msg(t, 0x602, "7F 31 78") for t in (1.1, 4, 5.9, 6.1)],
                        pending_timeout=5)[0]
        self.assertEqual(tx["status"], "PENDING_TIMEOUT")
        self.assertEqual(tx["response_pending_count"], 3)

    def test_wrong_id_sid_or_late_pending_cannot_extend_timeout(self):
        for negative in (msg(1.1, 0x613, "7F 31 78"), msg(1.1, 0x602, "7F 22 78"),
                         msg(2.1, 0x602, "7F 31 78")):
            with self.subTest(negative=negative):
                tx = self.match([msg(3, 0x602, "71 01 02 06")], [negative])[0]
                self.assertEqual(tx["status"], "TIMEOUT")

    def test_response_is_not_reused(self):
        txs = self.match([msg(3, 0x602, "71 01 02 06")],
                         [msg(1.1, 0x602, "7F 31 78")],
                         [msg(1, 0x682, "31 01 02 06"), msg(4, 0x682, "31 01 02 06")])
        self.assertEqual([tx["status"] for tx in txs], ["OK", "TIMEOUT"])

    def test_other_services_keep_identifier_matching(self):
        for request, positive in (("10 03", "50 03"), ("22 F1 90", "62 F1 90 00"),
                                  ("27 03", "67 03 11 22"), ("2E F1 90 00", "6E F1 90")):
            with self.subTest(request=request):
                tx = self.match([msg(1.2, 0x602, positive)],
                                requests=[msg(1, 0x682, request)])[0]
                self.assertEqual(tx["status"], "OK")

    def test_pending_summary_rows_and_excel(self):
        txs = self.match(negatives=[msg(1.1, 0x602, "7F 31 78")])
        rows = fn_build_transaction_rows(txs)
        self.assertEqual(rows[0]["Response"], "")
        self.assertEqual(rows[0]["Status"], "PENDING_TIMEOUT")
        reports = build_ecu_reports(txs)
        summary = build_summary_report(reports)
        self.assertEqual(summary[0]["timeout"], 1)
        self.assertEqual(summary[0]["pending_timeout"], 1)
        self.assertEqual(summary[0]["nrc_only"], 0)
        self.assertEqual(summary[0]["pending_count"], 1)
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
            path = Path(directory) / "report.xlsx"
            self.assertTrue(export_workbook(summary, reports, txs, path))
            workbook = load_workbook(path)
            try:
                self.assertIsNone(workbook["ALL_ECUS"]["E3"].value)
                self.assertEqual(workbook["ALL_ECUS"]["G3"].value, "PENDING_TIMEOUT")
                self.assertEqual(workbook["A"]["I3"].value, 1)
            finally:
                workbook.close()

    def test_asc_blf_txt_pipeline_pending_regression(self):
        vehicle = Vehicle(name="Test", ecus=[ECU(name="A", request_id="682", response_id="602")])
        records = [(1, 0x682, "04 31 01 02 06 AA AA AA"),
                   (1.1, 0x602, "03 7F 31 78 CC CC CC CC"),
                   (13, 0x602, "04 71 01 02 06 CC CC CC")]
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
            blf = Path(directory) / "pending.blf"
            with can.BLFWriter(str(blf)) as writer:
                for t, cid, data in records:
                    writer.on_message_received(can.Message(timestamp=1000+t, arbitration_id=cid,
                        is_extended_id=False, channel=0, data=bytes.fromhex(data)))
            blf_result = run_pipeline(str(blf), vehicle, channel=1)
            asc_result = run_pipeline(str(blf.with_suffix(".asc")), vehicle, channel=1)
            self.assertEqual(blf_result, asc_result)
            txt = blf.with_suffix(".txt")
            txt.write_text(HEADER + "".join(dsa_frame(
                timestamp=f"00:00:{int(t):02d}.{round((t % 1)*1000):03d}.000",
                can_id=f"{cid:X}", data=data) for t, cid, data in records), encoding="utf-8")
            for result in (blf_result, asc_result, run_pipeline(str(txt), vehicle, channel=0)):
                tx = result["transactions"][0]
                self.assertEqual(tx["status"], "OK")
                self.assertAlmostEqual(tx["response_time"], 12)
                self.assertEqual(tx["response_pending_count"], 1)


if __name__ == "__main__":
    unittest.main()
