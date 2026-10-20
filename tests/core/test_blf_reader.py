import errno
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import can
from can.io.blf import FILE_HEADER_STRUCT

from core.asc_reader import get_log_channels, load_log
from core.convert_blf import blf_to_asc
from core.pipeline import run_pipeline
from models.ecu import ECU
from models.vehicle import Vehicle


class BlfReaderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2])
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "input.blf"
        self.vehicle = Vehicle(name="Test", ecus=[ECU(name="ECU", request_id="682", response_id="602")])

    def write_messages(self, messages):
        with can.BLFWriter(self.path) as writer:
            for message in messages:
                writer.on_message_received(message)

    def message(self, time=1000, cid=0x682, data="03 22 F1 90 AA AA AA AA", channel=0, **flags):
        return can.Message(timestamp=time, arbitration_id=cid, channel=channel,
                           data=bytes.fromhex(data), is_extended_id=flags.pop("is_extended_id", False), **flags)

    def test_direct_read_does_not_create_asc(self):
        self.write_messages([self.message()])
        with patch("can.ASCWriter", side_effect=OSError(errno.ENOSPC, "No space left on device")) as writer:
            self.assertEqual(len(load_log(self.path)), 1)
        writer.assert_not_called()
        self.assertFalse(self.path.with_suffix(".asc").exists())

    def test_existing_user_asc_is_untouched(self):
        self.write_messages([self.message()])
        asc = self.path.with_suffix(".asc")
        asc.write_bytes(b"User-created ASC, do not overwrite")
        load_log(self.path)
        self.assertEqual(asc.read_bytes(), b"User-created ASC, do not overwrite")

    def test_channels_one_two_three_and_global_timestamp_origin(self):
        self.write_messages([self.message(1000 + index / 10, channel=index) for index in range(3)])
        self.assertEqual(get_log_channels(self.path), [1, 2, 3])
        for channel in (1, 2, 3):
            with self.subTest(channel=channel):
                messages = load_log(self.path, channel=channel)
                self.assertEqual(len(messages), 1)
                self.assertEqual(messages[0]["channel"], channel)
                self.assertAlmostEqual(messages[0]["timestamp"], (channel - 1) / 10)
        with self.assertRaisesRegex(ValueError, "Selected Diagnostic Channel"):
            load_log(self.path, channel=4)

    def test_classic_can_id_dlc_and_bytes_including_short_frames(self):
        self.write_messages([self.message(1000 + dlc, cid=0x123, data=" ".join("AB" for _ in range(dlc)))
                             for dlc in range(9)] +
                            [self.message(1010, cid=0x18DAF110, is_extended_id=True)])
        messages = load_log(self.path)
        self.assertEqual([item["dlc"] for item in messages], list(range(9)) + [8])
        for dlc, item in enumerate(messages[:9]):
            self.assertEqual(item["can_id"], 0x123)
            self.assertEqual(item["data"], [0xAB] * dlc)
            self.assertEqual(set(item), {"timestamp", "can_id", "channel", "dlc", "data"})
        self.assertEqual(messages[-1]["can_id"], 0x18DAF110)

    def test_unsupported_frames_do_not_reset_timestamp_origin(self):
        self.write_messages([self.message(1000, is_fd=True), self.message(1001, is_error_frame=True),
                             self.message(1002, data="", is_remote_frame=True, dlc=8),
                             self.message(1003)])
        with self.assertLogs("core.blf_reader", level="WARNING"):
            messages = load_log(self.path)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["timestamp"], 3)

    def test_blf_pipeline_equals_explicit_legacy_asc_including_pending_and_multiframe(self):
        records = [
            (1000.000001, 0x682, "04 31 01 02 06 AA AA AA"),
            (1000.100001, 0x602, "03 7F 31 78 CC CC CC CC"),
            (1013.000001, 0x602, "04 71 01 02 06 CC CC CC"),
            (1014.000001, 0x682, "03 22 F1 90 AA AA AA AA"),
            (1014.010001, 0x602, "10 0A 62 F1 90 11 22 33"),
            (1014.020001, 0x602, "21 44 55 66 77 CC CC CC"),
        ]
        self.write_messages([self.message(t, cid, data) for t, cid, data in records])
        before = self.path.read_bytes()
        direct = run_pipeline(str(self.path), self.vehicle, channel=1)
        self.assertFalse(self.path.with_suffix(".asc").exists())
        explicit_asc = blf_to_asc(self.path)
        self.assertEqual(direct, run_pipeline(explicit_asc, self.vehicle, channel=1))
        routine, did = direct["transactions"]
        self.assertEqual(routine["status"], "OK")
        self.assertAlmostEqual(routine["response_time"], 13)
        self.assertEqual(routine["response_pending_count"], 1)
        self.assertEqual(did["positive_response"]["payload"], "62 F1 90 11 22 33 44 55 66 77")
        self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_and_truncated_logs_fail_without_touching_asc(self):
        self.write_messages([self.message()])
        valid = self.path.read_bytes()
        asc = self.path.with_suffix(".asc")
        asc.write_bytes(b"keep")
        for contents in (b"", b"not BLF", valid[:40], valid[:-10]):
            with self.subTest(length=len(contents)):
                self.path.write_bytes(contents)
                for function in (load_log, get_log_channels):
                    with self.assertRaisesRegex(ValueError, "Invalid or truncated BLF"):
                        function(self.path)
                self.assertEqual(asc.read_bytes(), b"keep")

    def test_unreadable_log_has_context_and_preserves_errno(self):
        with patch("pathlib.Path.open", side_effect=PermissionError(errno.EACCES, "Access denied")):
            with self.assertRaisesRegex(OSError, "read BLF") as raised:
                load_log(self.path)
        self.assertEqual(raised.exception.errno, errno.EACCES)

    def test_truncated_final_object_is_not_silently_accepted(self):
        with can.BLFWriter(self.path, compression_level=0) as writer:
            writer.on_message_received(self.message())
        truncated = self.path.read_bytes()[:-8]
        header = list(FILE_HEADER_STRUCT.unpack_from(truncated))
        header[10] = len(truncated)
        self.path.write_bytes(FILE_HEADER_STRUCT.pack(*header) + truncated[FILE_HEADER_STRUCT.size:])
        with self.assertRaisesRegex(ValueError, "Invalid or truncated BLF"):
            load_log(self.path)

    def test_multiple_containers_are_read_in_bounded_chunks(self):
        self.write_messages([self.message(1000 + index / 1000) for index in range(10000)])
        source = self.path.open("rb")
        self.addCleanup(source.close)
        sizes = []

        class GuardedFile:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                source.close()

            def __getattr__(self, name):
                return getattr(source, name)

            def read(self, size=-1):
                if size < 0:
                    raise AssertionError("Unbounded raw BLF read")
                sizes.append(size)
                return source.read(size)

        with patch("pathlib.Path.open", return_value=GuardedFile()):
            messages = load_log(self.path)
        self.assertEqual(len(messages), 10000)
        self.assertGreater(len(sizes), 8)

    def test_timestamp_precision_matches_legacy_conversion(self):
        self.write_messages([self.message(1700000000.123456),
                             self.message(1700000000.1234574),
                             self.message(1700000000.9876543)])
        direct = load_log(self.path)
        asc = blf_to_asc(self.path)
        self.assertEqual(direct, load_log(asc))

    def test_legacy_conversion_enospc_location_is_asc_write(self):
        self.write_messages([self.message()])
        with patch("core.convert_blf.can.ASCWriter") as writer:
            writer.return_value.on_message_received.side_effect = OSError(errno.ENOSPC, "No space left on device")
            with self.assertRaises(OSError) as raised:
                blf_to_asc(self.path)
        self.assertEqual(raised.exception.errno, errno.ENOSPC)
        writer.assert_called_once_with(str(self.path.with_suffix(".asc")))


if __name__ == "__main__":
    unittest.main()
