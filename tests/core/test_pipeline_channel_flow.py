import tempfile
import unittest
from pathlib import Path
from unittest.mock import ANY, patch

from core.pipeline import run_pipeline
from gui.controllers.analysis_controller import AnalysisController


class PipelineChannelFlowTests(unittest.TestCase):

    def test_run_pipeline_passes_channel_to_log_loader(self):
        with (
            patch("core.pipeline.load_log", return_value=[]) as load_log,
            patch(
                "core.pipeline.load_vehicle_mapping",
                return_value=({"ECU": {}}, {}, {}),
            ),
            patch("core.pipeline.reassemble_isotp", return_value=[]),
            patch("core.pipeline.extract_requests", return_value=[]),
            patch("core.pipeline.extract_negative_responses", return_value=[]),
            patch("core.pipeline.extract_positive_responses", return_value=[]),
            patch("core.pipeline.build_transactions_v4", return_value=[]),
            patch("core.pipeline.build_ecu_reports", return_value=[]),
            patch("core.pipeline.build_summary_report", return_value={}),
        ):
            result = run_pipeline("demo.asc", object(), channel=2)

        load_log.assert_called_once_with("demo.asc", channel=2)
        self.assertEqual(result["transactions"], [])

    def test_analysis_controller_passes_channel_to_pipeline(self):
        handle = tempfile.NamedTemporaryFile(suffix=".asc", delete=False)
        handle.close()
        self.addCleanup(Path(handle.name).unlink, missing_ok=True)

        controller = AnalysisController()

        with patch(
            "gui.controllers.analysis_controller.run_pipeline",
            return_value={"transactions": []},
        ) as pipeline:
            result = controller.fn_run(
                log_file=handle.name,
                vehicle=object(),
                channel=2,
            )

        pipeline.assert_called_once_with(
            asc_file=handle.name,
            vehicle=ANY,
            channel=2,
        )
        self.assertEqual(result, {"transactions": []})

    def test_analysis_controller_requires_channel(self):
        controller = AnalysisController()

        with self.assertRaisesRegex(ValueError, "Diagnostic Channel"):
            controller.fn_run(
                log_file="demo.asc",
                vehicle=object(),
                channel=None,
            )


if __name__ == "__main__":
    unittest.main()
