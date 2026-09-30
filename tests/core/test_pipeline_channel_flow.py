import tempfile
import unittest
from pathlib import Path
from unittest.mock import ANY, patch

import core.pipeline as pipeline_module
import gui.controllers.analysis_controller as analysis_controller_module


class PipelineChannelFlowTests(unittest.TestCase):

    def test_run_pipeline_passes_channel_to_log_loader(self):
        with (
            patch.object(pipeline_module, "load_log", return_value=[]) as load_log,
            patch.object(
                pipeline_module,
                "load_vehicle_mapping",
                return_value=({"ECU": {}}, {}, {}),
            ),
            patch.object(pipeline_module, "reassemble_isotp", return_value=[]),
            patch.object(pipeline_module, "extract_requests", return_value=[]),
            patch.object(pipeline_module, "extract_negative_responses", return_value=[]),
            patch.object(pipeline_module, "extract_positive_responses", return_value=[]),
            patch.object(pipeline_module, "build_transactions_v4", return_value=[]),
            patch.object(pipeline_module, "build_ecu_reports", return_value=[]),
            patch.object(pipeline_module, "build_summary_report", return_value={}),
        ):
            result = pipeline_module.run_pipeline("demo.asc", object(), channel=2)

        load_log.assert_called_once_with("demo.asc", channel=2)
        self.assertEqual(result["transactions"], [])

    def test_analysis_controller_passes_channel_to_pipeline(self):
        handle = tempfile.NamedTemporaryFile(suffix=".asc", delete=False)
        handle.close()
        self.addCleanup(Path(handle.name).unlink, missing_ok=True)

        controller = analysis_controller_module.AnalysisController()

        with patch.object(
            analysis_controller_module,
            "run_pipeline",
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
            logger=None,
        )
        self.assertEqual(result, {"transactions": []})


    def test_analysis_controller_passes_logger_to_pipeline(self):
        handle = tempfile.NamedTemporaryFile(suffix=".asc", delete=False)
        handle.close()
        self.addCleanup(Path(handle.name).unlink, missing_ok=True)

        controller = analysis_controller_module.AnalysisController()
        statuses = []

        with patch.object(
            analysis_controller_module,
            "run_pipeline",
            return_value={"transactions": []},
        ) as pipeline:
            controller.fn_run(
                log_file=handle.name,
                vehicle=object(),
                channel=2,
                logger=statuses.append,
            )

        pipeline.assert_called_once_with(
            asc_file=handle.name,
            vehicle=ANY,
            channel=2,
            logger=statuses.append,
        )

    def test_run_pipeline_reports_reading_selected_channel_before_loading_log(self):
        statuses = []

        with (
            patch.object(pipeline_module, "load_log", return_value=[]) as load_log,
            patch.object(
                pipeline_module,
                "load_vehicle_mapping",
                return_value=({"ECU": {}}, {}, {}),
            ),
            patch.object(pipeline_module, "reassemble_isotp", return_value=[]),
            patch.object(pipeline_module, "extract_requests", return_value=[]),
            patch.object(pipeline_module, "extract_negative_responses", return_value=[]),
            patch.object(pipeline_module, "extract_positive_responses", return_value=[]),
            patch.object(pipeline_module, "build_transactions_v4", return_value=[]),
            patch.object(pipeline_module, "build_ecu_reports", return_value=[]),
            patch.object(pipeline_module, "build_summary_report", return_value={}),
        ):
            pipeline_module.run_pipeline("demo.asc", object(), channel=2, logger=statuses.append)

        self.assertEqual(statuses[0], "Reading Channel 2...")
        load_log.assert_called_once_with("demo.asc", channel=2)

    def test_analysis_controller_requires_channel(self):
        controller = analysis_controller_module.AnalysisController()

        with self.assertRaisesRegex(ValueError, "Diagnostic Channel"):
            controller.fn_run(
                log_file="demo.asc",
                vehicle=object(),
                channel=None,
            )


if __name__ == "__main__":
    unittest.main()
