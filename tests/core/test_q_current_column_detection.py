import unittest

from core.q_current_column_detection import (
    CURRENT_COLUMN_KEYWORDS,
    TIME_COLUMN_KEYWORDS,
    AmbiguousColumnError,
    _find_column,
    _normalize_header,
)


class QCurrentColumnDetectionTests(unittest.TestCase):

    def test_normalize_header_trims_lowercases_and_collapses_whitespace(self):
        self.assertEqual(_normalize_header(" Trigger Time "), "trigger time")
        self.assertEqual(_normalize_header("NO1   Average   Ch2"), "no1 average ch2")
        self.assertEqual(_normalize_header("CURRENT"), "current")

    def test_detects_trigger_time_and_average_channel(self):
        columns = ["Trigger time", "No1 Average Ch1"]

        self.assertEqual(_find_column(columns, TIME_COLUMN_KEYWORDS), "Trigger time")
        self.assertEqual(_find_column(columns, CURRENT_COLUMN_KEYWORDS), "No1 Average Ch1")

    def test_detects_simple_time_and_current_exact_headers(self):
        columns = ["Time", "Current"]

        self.assertEqual(_find_column(columns, TIME_COLUMN_KEYWORDS), "Time")
        self.assertEqual(_find_column(columns, CURRENT_COLUMN_KEYWORDS), "Current")

    def test_detects_timestamp_and_average_ch20(self):
        columns = ["Timestamp", "No1 Average Ch20"]

        self.assertEqual(_find_column(columns, TIME_COLUMN_KEYWORDS), "Timestamp")
        self.assertEqual(_find_column(columns, CURRENT_COLUMN_KEYWORDS), "No1 Average Ch20")

    def test_keyword_priority_beats_first_column_order(self):
        columns = ["Trigger time", "Voltage Average", "Current Average"]

        self.assertEqual(_find_column(columns, CURRENT_COLUMN_KEYWORDS), "Current Average")

    def test_same_keyword_same_priority_is_ambiguous(self):
        columns = ["Trigger time", "No1 Average Ch1", "No1 Average Ch2"]

        with self.assertRaises(AmbiguousColumnError) as context:
            _find_column(columns, CURRENT_COLUMN_KEYWORDS)

        self.assertEqual(context.exception.keyword, "average")
        self.assertEqual(
            context.exception.candidates,
            ["No1 Average Ch1", "No1 Average Ch2"],
        )


if __name__ == "__main__":
    unittest.main()
