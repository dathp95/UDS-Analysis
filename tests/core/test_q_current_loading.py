import unittest
from types import SimpleNamespace

from core.q_current_loading import calculate_elapsed_seconds, prepare_workspace_data, timed_call


class QCurrentLoadingTests(unittest.TestCase):
    def samples(self, *times):
        return [SimpleNamespace(time=value, current_mA=1) for value in times]

    def test_elapsed_and_bounds_preserve_unsorted_source_order(self):
        samples = self.samples("10", "12", "9")
        prepared = prepare_workspace_data(samples)
        self.assertIs(prepared.samples, samples)
        self.assertEqual(prepared.elapsed_seconds, [0, 2, -1])
        self.assertEqual(prepared.time_bounds, (-1, 2))

    def test_timestamp_format_and_mixed_time_errors_are_preserved(self):
        self.assertEqual(calculate_elapsed_seconds(self.samples(
            "26-09-11 11:41:29.036", "26-09-11 11:41:30.079")), [0, 1.043])
        prepared = prepare_workspace_data(self.samples("0", "2026-10-24 00:00:00"))
        self.assertIsNone(prepared.time_bounds)
        self.assertIsNone(prepared.elapsed_seconds)
        self.assertIn("mixed timestamp formats", prepared.timestamp_error)
        invalid = prepare_workspace_data(self.samples("bad"))
        self.assertIn("Unsupported timestamp", invalid.timestamp_error)

    def test_empty_data_has_no_range(self):
        prepared = prepare_workspace_data([])
        self.assertEqual(prepared.elapsed_seconds, [])
        self.assertIsNone(prepared.time_bounds)

    def test_timing_records_success_and_failure_without_swallowing_errors(self):
        timings = {}
        self.assertEqual(timed_call(timings, "stage", lambda: 42), 42)
        self.assertGreaterEqual(timings["stage"], 0)

        def fail():
            raise ValueError("failed")

        with self.assertRaisesRegex(ValueError, "failed"):
            timed_call(timings, "error", fail)
        self.assertGreaterEqual(timings["error"], 0)
