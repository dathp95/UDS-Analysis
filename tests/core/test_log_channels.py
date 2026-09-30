import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from core.asc_reader import get_log_channels, load_asc, load_log, parse_asc_line


class AscReaderChannelTests(unittest.TestCase):

    def _write_asc(self, content: str) -> Path:
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".asc",
            encoding="utf-8",
            delete=False,
        )
        self.addCleanup(Path(handle.name).unlink, missing_ok=True)
        handle.write(content)
        handle.close()
        return Path(handle.name)

    def test_parse_asc_line_includes_channel(self):
        msg = parse_asc_line(
            "0.001 2 681 Rx d 8 03 22 F1 90 00 00 00 00"
        )

        self.assertEqual(msg["timestamp"], 0.001)
        self.assertEqual(msg["channel"], 2)
        self.assertEqual(msg["can_id"], 0x681)
        self.assertEqual(msg["dlc"], 8)
        self.assertEqual(msg["data"], [3, 0x22, 0xF1, 0x90, 0, 0, 0, 0])

    def test_parse_asc_line_rejects_invalid_channel(self):
        self.assertIsNone(
            parse_asc_line("0.001 DIAG 681 Rx d 8 03 22 F1 90 00 00 00 00")
        )

    def test_get_log_channels_returns_unique_sorted_asc_channels(self):
        log_file = self._write_asc(
            "header\n"
            "0.001 2 681 Rx d 8 03 22 F1 90 00 00 00 00\n"
            "0.002 1 682 Rx d 8 03 22 F1 91 00 00 00 00\n"
            "0.003 2 683 Rx d 8 03 22 F1 92 00 00 00 00\n"
            "0.004 4 684 Rx d 8 03 22 F1 93 00 00 00 00\n"
        )

        self.assertEqual(get_log_channels(log_file), [1, 2, 4])

    def test_load_asc_filters_selected_channel_while_reading(self):
        log_file = self._write_asc(
            "0.001 1 681 Rx d 8 03 22 F1 90 00 00 00 00\n"
            "0.002 2 682 Rx d 8 03 22 F1 91 00 00 00 00\n"
            "0.003 2 683 Rx d 8 03 22 F1 92 00 00 00 00\n"
        )

        messages = load_asc(log_file, channel=2)

        self.assertEqual([msg["channel"] for msg in messages], [2, 2])
        self.assertEqual([msg["can_id"] for msg in messages], [0x682, 0x683])

    def test_load_asc_raises_when_selected_channel_is_not_present(self):
        log_file = self._write_asc(
            "0.001 1 681 Rx d 8 03 22 F1 90 00 00 00 00\n"
        )

        with self.assertRaisesRegex(ValueError, "Selected Diagnostic Channel"):
            load_asc(log_file, channel=2)

    def test_get_log_channels_uses_blf_metadata_without_converting(self):
        with (
            patch("core.asc_reader.get_blf_channels", return_value=[3, 1]) as blf_channels,
            patch("core.asc_reader.blf_to_asc") as blf_to_asc,
        ):
            self.assertEqual(get_log_channels("demo.blf"), [3, 1])

        blf_channels.assert_called_once_with("demo.blf")
        blf_to_asc.assert_not_called()

    def test_load_log_filters_converted_blf_with_logical_channel(self):
        with (
            patch("core.asc_reader.blf_to_asc", return_value="demo.asc") as blf_to_asc,
            patch("core.asc_reader.load_asc", return_value=[{"channel": 2}]) as asc,
        ):
            self.assertEqual(load_log("demo.blf", channel=2), [{"channel": 2}])

        blf_to_asc.assert_called_once_with("demo.blf")
        asc.assert_called_once_with("demo.asc", channel=2)


class BlfChannelDiscoveryTests(unittest.TestCase):

    def test_get_blf_channels_normalizes_raw_zero_based_channels(self):
        from core.convert_blf import get_blf_channels

        messages = [
            Mock(channel=1),
            Mock(channel=0),
            Mock(channel=1),
            Mock(channel=None),
        ]

        with patch("core.convert_blf.can.BLFReader", return_value=messages):
            self.assertEqual(get_blf_channels("demo.blf"), [1, 2])


if __name__ == "__main__":
    unittest.main()
