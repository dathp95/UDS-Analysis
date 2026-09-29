import unittest

from core.q_current_analysis import (
    CurrentClassification,
    analyze_q_current,
    classify_current,
)


class QCurrentAnalysisTests(unittest.TestCase):

    def test_classifies_current_by_magnitude(self):
        self.assertEqual(
            classify_current(-30.0, 30.0, 300.0),
            CurrentClassification.NORMAL_SLEEP,
        )
        self.assertEqual(
            classify_current(-30.1, 30.0, 300.0),
            CurrentClassification.WAKE_UP_CANDIDATE,
        )
        self.assertEqual(
            classify_current(300.1, 30.0, 300.0),
            CurrentClassification.EXCLUDED,
        )

    def test_average_sleep_current_uses_magnitude_inside_wake_limit(self):
        result = analyze_q_current(
            [0.0, 1.0, 2.0, 3.0],
            [-10.0, -40.0, 400.0, 20.0],
            standard_current_ma=30.0,
            wake_up_limit_ma=300.0,
            wake_duration_s=2.0,
        )

        self.assertAlmostEqual(result.average_sleep_current_ma, 70.0 / 3.0)
        self.assertEqual(result.minimum_sleep_current_ma, 10.0)
        self.assertEqual(result.maximum_sleep_current_ma, 40.0)

    def test_passes_when_average_sleep_current_is_at_or_below_standard(self):
        result = analyze_q_current(
            [0.0, 1.0, 2.0],
            [10.0, -20.0, 30.0],
            standard_current_ma=30.0,
            wake_up_limit_ma=300.0,
            wake_duration_s=2.0,
        )

        self.assertEqual(result.result_status, "PASSED")

    def test_fails_when_average_sleep_current_is_above_standard(self):
        result = analyze_q_current(
            [0.0, 1.0, 2.0],
            [10.0, -50.0, 60.0],
            standard_current_ma=30.0,
            wake_up_limit_ma=300.0,
            wake_duration_s=2.0,
        )

        self.assertEqual(result.result_status, "FAILED")

    def test_fails_when_no_analyzable_samples_exist(self):
        result = analyze_q_current(
            [0.0, 1.0],
            [400.0, -500.0],
            standard_current_ma=30.0,
            wake_up_limit_ma=300.0,
            wake_duration_s=2.0,
        )

        self.assertEqual(result.result_status, "FAILED")
        self.assertIsNone(result.average_sleep_current_ma)

    def test_detects_only_wake_candidates_that_meet_duration(self):
        result = analyze_q_current(
            [0.0, 1.0, 2.0, 3.5, 5.0, 6.0, 6.5],
            [10.0, -31.0, -32.0, -45.0, 20.0, 100.0, 110.0],
            standard_current_ma=30.0,
            wake_up_limit_ma=300.0,
            wake_duration_s=2.0,
        )

        self.assertEqual(result.wake_up_event_count, 1)
        self.assertEqual(result.wake_up_intervals[0].start_s, 1.0)
        self.assertEqual(result.wake_up_intervals[0].end_s, 3.5)
        self.assertEqual(result.wake_up_intervals[0].duration_s, 2.5)
        self.assertEqual(result.wake_up_intervals[0].peak_current_ma, 45.0)

    def test_above_wake_limit_breaks_candidate_region(self):
        result = analyze_q_current(
            [0.0, 1.0, 2.0, 3.0, 4.0],
            [10.0, 40.0, 400.0, 45.0, 50.0],
            standard_current_ma=30.0,
            wake_up_limit_ma=300.0,
            wake_duration_s=1.0,
        )

        self.assertEqual(result.wake_up_event_count, 1)
        self.assertEqual(result.wake_up_intervals[0].start_s, 3.0)
        self.assertEqual(result.wake_up_intervals[0].end_s, 4.0)

    def test_multiple_wake_intervals_report_interval_statistics(self):
        result = analyze_q_current(
            [0, 1, 3, 4, 10, 11, 13],
            [10, 40, 50, 10, 60, 70, 20],
            standard_current_ma=30,
            wake_up_limit_ma=300,
            wake_duration_s=1,
        )

        self.assertEqual(result.wake_up_event_count, 2)
        self.assertEqual(result.total_wake_up_duration_s, 3.0)
        self.assertEqual(result.average_wake_up_duration_s, 1.5)
        self.assertEqual(result.maximum_wake_up_duration_s, 2.0)
        self.assertEqual(result.average_wake_up_interval_s, 7.0)
        self.assertEqual(result.minimum_wake_up_interval_s, 7.0)
        self.assertEqual(result.maximum_wake_up_interval_s, 7.0)

    def test_longest_continuous_sleep_excludes_wake_events_and_out_of_range(self):
        result = analyze_q_current(
            [0, 2, 4, 6, 8, 10, 12],
            [10, 20, 40, 50, 400, 20, 25],
            standard_current_ma=30,
            wake_up_limit_ma=300,
            wake_duration_s=2,
        )

        self.assertEqual(result.longest_continuous_sleep_s, 2.0)

    def test_test_information_uses_actual_time_range_and_median_interval(self):
        result = analyze_q_current(
            [10.0, 13.0, 11.0, 17.0],
            [1.0, 2.0, 3.0, 4.0],
            standard_current_ma=30.0,
            wake_up_limit_ma=300.0,
            wake_duration_s=2.0,
        )

        self.assertEqual(result.start_time_s, 10.0)
        self.assertEqual(result.end_time_s, 17.0)
        self.assertEqual(result.duration_s, 7.0)
        self.assertEqual(result.total_samples, 4)
        self.assertEqual(result.sample_interval_s, 2.0)

    def test_preserves_source_time_metadata_in_elapsed_sort_order(self):
        result = analyze_q_current(
            [10.0, 0.0],
            [20.0, 10.0],
            standard_current_ma=30.0,
            wake_up_limit_ma=300.0,
            wake_duration_s=2.0,
            source_times=[
                "2026-09-29 11:23:11.750",
                "2026-09-29 10:23:22.125",
            ],
        )

        self.assertEqual(result.source_start_time, "2026-09-29 10:23:22.125")
        self.assertEqual(result.source_end_time, "2026-09-29 11:23:11.750")

    def test_sample_interval_is_none_for_single_sample(self):
        result = analyze_q_current(
            [10.0],
            [1.0],
            standard_current_ma=30.0,
            wake_up_limit_ma=300.0,
            wake_duration_s=2.0,
        )

        self.assertIsNone(result.sample_interval_s)

    def test_empty_input_returns_failed_empty_result(self):
        result = analyze_q_current(
            [],
            [],
            standard_current_ma=30.0,
            wake_up_limit_ma=300.0,
            wake_duration_s=2.0,
        )

        self.assertEqual(result.result_status, "FAILED")
        self.assertEqual(result.total_samples, 0)
        self.assertEqual(result.wake_up_intervals, ())

    def test_zip_alignment_ignores_unpaired_values(self):
        result = analyze_q_current(
            [0.0, 1.0, 2.0],
            [10.0, 20.0],
            standard_current_ma=30.0,
            wake_up_limit_ma=300.0,
            wake_duration_s=2.0,
        )

        self.assertEqual(result.total_samples, 2)
        self.assertEqual(result.duration_s, 1.0)

    def test_wake_duration_uses_elapsed_time_not_sample_count(self):
        result = analyze_q_current(
            [0.0, 10.0],
            [40.0, 50.0],
            standard_current_ma=30.0,
            wake_up_limit_ma=300.0,
            wake_duration_s=5.0,
        )

        self.assertEqual(result.wake_up_event_count, 1)
        self.assertEqual(result.wake_up_intervals[0].duration_s, 10.0)


if __name__ == "__main__":
    unittest.main()
