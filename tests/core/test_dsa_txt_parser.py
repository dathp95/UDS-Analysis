import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from core.asc_reader import get_log_channels, load_log


HEADER = "#!DSAVci.log\n$Log.Format.String = DSA-TEXT\n"


def dsa_frame(timestamp="00:00:21.094.197", channel=0, can_id="00000602",
              data="03 7f 22 78 cc cc cc cc", dlc=8, direction="-R--------------", frame_type="11n"):
    return (f"[{timestamp}] 0x00000003 Ch{channel:03d}(CAN) F:000 T:000 Msg "
            f"{direction} E:0x0000 {frame_type} {dlc:02d} id:0x{can_id} >{data}<\n")


class DSATextParserTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2])
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "log.txt"

    def write(self, content):
        self.path.write_text(content, encoding="utf-8")
        return self.path

    def test_structured_diagnostics_account_for_every_can_record_without_leaking_data(self):
        from core.log_parsers.diagnostics import ParserDiagnostics
        private = "PRIVATE_DIAGNOSTIC_CONTENT"
        self.write(HEADER + "$Log.Channels = 2\n$Log.Ch000.BusType = CAN_HS\n"
                   + "$Log.Ch000.BaudRate = 500000 [Baud]\n"
                   + dsa_frame(channel=0) + dsa_frame(channel=3)
                   + dsa_frame(dlc=7) + dsa_frame(frame_type=private)
                   + "Ch000(CAN) Unhandled record\n# ordinary comment\n")
        diagnostics = ParserDiagnostics()
        with self.assertLogs("core.log_parsers.dsa_txt_parser", level="WARNING") as logs:
            messages = load_log(self.path, channel=0, diagnostics=diagnostics)
        self.assertEqual(len(messages), 1)
        self.assertEqual(diagnostics.total_can_records, 5)
        self.assertEqual(diagnostics.parsed_frames, 2)
        self.assertEqual(diagnostics.malformed_frames, 1)
        self.assertEqual(diagnostics.unsupported_frames, 1)
        self.assertEqual(diagnostics.other_skipped_can_frames, 1)
        self.assertEqual(diagnostics.total_can_records, diagnostics.parsed_frames + diagnostics.skipped_frames)
        self.assertEqual(diagnostics.channels, [0, 3])
        self.assertEqual(diagnostics.frames_by_channel, {0: 1, 3: 1})
        self.assertEqual(diagnostics.selected_channel, 0)
        self.assertEqual(diagnostics.selected_channel_frames, 1)
        self.assertEqual(diagnostics.pipeline_frames, 0)
        self.assertEqual(diagnostics.declared_channel_count, 2)
        self.assertEqual(diagnostics.bus_types, {0: "CAN_HS"})
        self.assertEqual(diagnostics.baud_rates, {0: 500000})
        self.assertTrue(diagnostics.scan_complete)
        self.assertTrue(diagnostics.has_warnings)
        self.assertNotIn(private, str(diagnostics))
        self.assertNotIn(private, str(logs.output))
        self.assertNotIn(str(self.path), str(logs.output))
        self.assertEqual(set(messages[0]), {"timestamp", "channel", "can_id", "dlc", "data"})

    def test_diagnostics_preserve_timestamp_precision_order_and_discontinuities(self):
        from core.log_parsers.diagnostics import ParserDiagnostics
        self.write(HEADER + dsa_frame(timestamp="00:00:22.915.223")
                   + dsa_frame(timestamp="00:00:22.919.897")
                   + dsa_frame(timestamp="00:00:21.000.001"))
        diagnostics = ParserDiagnostics()
        with self.assertLogs("core.log_parsers.dsa_txt_parser", level="WARNING"):
            messages = load_log(self.path, channel=0, diagnostics=diagnostics)
        self.assertAlmostEqual((messages[1]["timestamp"] - messages[0]["timestamp"]) * 1000, 4.674, places=9)
        self.assertEqual(diagnostics.timestamp_discontinuities, 1)
        self.assertEqual(diagnostics.first_timestamp, 22.915223)
        self.assertEqual(diagnostics.last_timestamp, 21.000001)
        self.assertEqual(messages[-1]["timestamp"], 21.000001)

    def test_diagnostics_reset_per_call_and_errors_stay_at_file_level(self):
        from core.log_parsers.diagnostics import ParserDiagnostics
        diagnostics = ParserDiagnostics()
        malformed = dsa_frame().replace("Ch000(CAN)", "Ch?(CAN)")
        self.write(HEADER + malformed * 20 + dsa_frame())
        with self.assertLogs("core.log_parsers.dsa_txt_parser", level="WARNING"):
            self.assertEqual(get_log_channels(self.path, diagnostics=diagnostics), [0])
        self.assertEqual(diagnostics.malformed_frames, 20)
        self.assertEqual(diagnostics.frames_by_channel, {0: 1})
        self.assertLessEqual(len(diagnostics.examples), 5)
        self.write(HEADER + dsa_frame(channel=1))
        get_log_channels(self.path, diagnostics=diagnostics)
        self.assertEqual(diagnostics.parsed_frames, 1)
        self.assertEqual(diagnostics.malformed_frames, 0)
        self.assertEqual(diagnostics.channels, [1])
        self.assertFalse(diagnostics.has_warnings)
        self.write("Unsupported header\n")
        with self.assertRaises(ValueError):
            get_log_channels(self.path, diagnostics=diagnostics)
        self.assertFalse(diagnostics.scan_complete)
        self.assertEqual(diagnostics.parsed_frames, 0)

    def test_no_valid_frames_still_populates_failure_diagnostics(self):
        from core.log_parsers.diagnostics import ParserDiagnostics
        self.write(HEADER + dsa_frame(dlc=7) + dsa_frame(frame_type="29n"))
        diagnostics = ParserDiagnostics()
        with self.assertLogs("core.log_parsers.dsa_txt_parser", level="WARNING"):
            with self.assertRaisesRegex(ValueError, "No valid.*CAN"):
                get_log_channels(self.path, diagnostics=diagnostics)
        self.assertEqual(diagnostics.total_can_records, 2)
        self.assertEqual(diagnostics.parsed_frames, 0)
        self.assertEqual(diagnostics.malformed_frames, 1)
        self.assertEqual(diagnostics.unsupported_frames, 1)

    def test_missing_channel_is_file_level_error_and_lin_is_not_a_can_error(self):
        from core.log_parsers.diagnostics import ParserDiagnostics
        self.write(HEADER + dsa_frame() + dsa_frame().replace("Ch000(CAN)", "")
                   + dsa_frame().replace("(CAN)", "(LIN)"))
        diagnostics = ParserDiagnostics()
        with self.assertLogs("core.log_parsers.dsa_txt_parser", level="WARNING"):
            get_log_channels(self.path, diagnostics=diagnostics)
        self.assertEqual(diagnostics.total_can_records, 2)
        self.assertEqual(diagnostics.malformed_frames, 1)
        self.assertEqual(diagnostics.frames_by_channel, {0: 1})

    def test_detects_both_signatures_with_bom_and_assignment_whitespace(self):
        from core.log_parsers.dsa_txt_parser import DSATextParser
        from core.log_parsers.registry import detect_txt_parser
        self.write("\ufeff  #!DSAVci.log  \n\t$Log.Format.String\t =\tDSA-TEXT  \n" + dsa_frame())
        self.assertIsInstance(detect_txt_parser(self.path), DSATextParser)
        self.assertEqual(get_log_channels(self.path), [0])

    def test_rejects_empty_unknown_and_incomplete_headers(self):
        for content in ("", " \n", "Other TXT log\n", "#!DSAVci.log\n", "$Log.Format.String = DSA-TEXT\n"):
            with self.subTest(content=content):
                self.write(content)
                with self.assertRaisesRegex(ValueError, "empty|Unsupported|header"):
                    get_log_channels(self.path)

    def test_parser_contract_accepts_raw_crlf_header_and_registry_can_be_extended(self):
        from core.log_parsers.dsa_txt_parser import DSATextParser
        from core.log_parsers.registry import detect_txt_parser
        self.assertTrue(DSATextParser().can_parse(HEADER.replace("\n", "\r\n")))
        self.write("Example future format\n")
        registered = Mock()
        registered.can_parse.return_value = True
        with patch("core.log_parsers.registry.TXT_PARSERS", [registered]):
            self.assertIs(detect_txt_parser(self.path), registered)
        registered.can_parse.assert_called_once_with("Example future format\n")

    def test_detection_reads_only_a_bounded_header(self):
        from core.log_parsers.registry import detect_txt_parser
        self.write(HEADER + dsa_frame() * 500)
        reads = []
        real_open = Path.open

        class BoundedRead:
            def __init__(self, file):
                self.file = file
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.file.close()
            def read(self, size=-1):
                reads.append(size)
                if size <= 0 or size > 65536:
                    raise AssertionError("Format detection must read a bounded prefix")
                return self.file.read(size)
            def __iter__(self):
                return iter(self.file)

        with patch.object(Path, "open", lambda path, *a, **kw: BoundedRead(real_open(path, *a, **kw))):
            detect_txt_parser(self.path)
        self.assertEqual(len(reads), 1)
        reads.clear()
        with patch.object(Path, "open", lambda path, *a, **kw: BoundedRead(real_open(path, *a, **kw))):
            self.assertEqual(get_log_channels(self.path), [0])
            self.assertEqual(len(load_log(self.path)), 500)
        self.assertTrue(all(0 < size <= 65536 for size in reads))

    def test_normalized_contract_and_padding_are_preserved_without_conversion(self):
        self.write(HEADER + dsa_frame())
        with patch("core.asc_reader.blf_to_asc") as convert:
            messages = load_log(self.path, channel=0)
        convert.assert_not_called()
        self.assertEqual(messages, [{"timestamp": 21.094197, "channel": 0,
                                    "can_id": 0x602, "dlc": 8,
                                    "data": [3, 0x7F, 0x22, 0x78, 0xCC, 0xCC, 0xCC, 0xCC]}])
        self.assertEqual(list(Path(self.directory.name).iterdir()), [self.path])

    def test_timestamps_hex_case_spacing_and_both_directions(self):
        records = [dsa_frame(timestamp=t, direction=d, data="03 7F 22 78 CC cc CC cc")
                   for t, d in (("00:00:20.925.490", "T---------------"),
                                ("00:00:22.915.223", "-R--------------"),
                                ("00:00:22.919.897", "-R--------------"),
                                ("01:02:03.004.005", "T---------------"))]
        self.write(HEADER + "".join(line.replace(" ", "  \t") for line in records))
        messages = load_log(self.path)
        for msg, expected in zip(messages, (20.925490, 22.915223, 22.919897, 3723.004005)):
            self.assertAlmostEqual(msg["timestamp"], expected, places=9)
        self.assertEqual(len(messages), 4)

    def test_nonconsecutive_channels_are_observed_and_selected_zero_is_not_rebased(self):
        self.write(HEADER + "".join(dsa_frame(channel=ch) for ch in (3, 1, 0, 3)))
        self.assertEqual(get_log_channels(self.path), [0, 1, 3])
        self.assertEqual([m["channel"] for m in load_log(self.path, channel=1)], [1])
        self.assertEqual([m["channel"] for m in load_log(self.path, channel=0)], [0])
        with self.assertRaisesRegex(ValueError, "Selected Diagnostic Channel.*not found"):
            load_log(self.path, channel=2)

    def test_metadata_disagreement_uses_observed_valid_channels(self):
        self.write(HEADER + "$Log.Channels = 1\n$Log.Ch000.BusType = CAN_HS\n" + dsa_frame(channel=3))
        with self.assertLogs("core.log_parsers.dsa_txt_parser", level="WARNING") as logs:
            self.assertEqual(get_log_channels(self.path), [3])
        self.assertIn("header", " ".join(logs.output).lower())

    def test_dlc_zero_to_eight_and_can_id_boundary(self):
        self.write(HEADER + "".join(dsa_frame(dlc=n, data=" ".join(["AA"] * n), can_id="7FF") for n in range(9)))
        messages = load_log(self.path)
        self.assertEqual([m["dlc"] for m in messages], list(range(9)))
        self.assertEqual(messages[0]["data"], [])
        self.assertTrue(all(m["can_id"] == 0x7FF for m in messages))

    def test_malformed_and_unsupported_records_are_skipped_with_bounded_diagnostics(self):
        bad = [dsa_frame(timestamp="00:60:21.094.197"), dsa_frame(timestamp="00:00:60.094.197"),
               dsa_frame(can_id="20000000"), dsa_frame(can_id="800"),
               dsa_frame(dlc=9), dsa_frame(dlc=7), dsa_frame(data="03 7F 22 78 CC CC CC GG"),
               dsa_frame(frame_type="CANFD"), dsa_frame(frame_type="29n"),
               dsa_frame().replace("[00:00:21.094.197]", "[broken]"),
               dsa_frame(channel=-1), dsa_frame().replace(" Msg ", " ")]
        self.write(HEADER + "".join(bad * 20) + dsa_frame(channel=1))
        with self.assertLogs("core.log_parsers.dsa_txt_parser", level="WARNING") as logs:
            self.assertEqual(get_log_channels(self.path), [1])
        self.assertLessEqual(len(logs.output), 2)
        self.assertIn(str(len(bad) * 20), " ".join(logs.output))
        self.assertIn("line", " ".join(logs.output).lower())

    def test_empty_can_log_fails_and_non_can_lines_are_ignored(self):
        self.write(HEADER + "\n# comment\nInformational record\n" + dsa_frame().replace("(CAN)", "(LIN)"))
        with self.assertRaisesRegex(ValueError, "No valid.*CAN"):
            load_log(self.path)
        with self.assertRaisesRegex(ValueError, "No valid.*CAN"):
            get_log_channels(self.path)

    def test_decoding_permission_and_missing_file_errors_are_not_silenced(self):
        self.path.write_bytes(HEADER.encode() + b"\xff")
        with self.assertRaisesRegex(ValueError, "UTF-8|decod"):
            get_log_channels(self.path)
        self.path.write_bytes(HEADER.encode() + b"# comment\n" * 2000 + b"\xff")
        with self.assertRaisesRegex(ValueError, "UTF-8|decod"):
            load_log(self.path)
        self.write(HEADER + dsa_frame())
        with patch.object(Path, "open", side_effect=PermissionError("Permission denied")):
            with self.assertRaisesRegex(PermissionError, "Permission denied"):
                get_log_channels(self.path)
        self.path.unlink()
        with self.assertRaises(FileNotFoundError):
            load_log(self.path)


if __name__ == "__main__":
    unittest.main()
