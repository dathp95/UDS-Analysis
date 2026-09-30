import os
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gui.workers.analysis_worker import AnalysisWorker


class AnalysisWorkerTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_worker_emits_status_and_finished_result(self):
        controller = Mock()
        controller.fn_run.side_effect = lambda **kwargs: (
            kwargs["logger"]("Reading log..."),
            {"transactions": []},
        )[1]
        worker = AnalysisWorker(
            controller=controller,
            log_file="demo.asc",
            vehicle=object(),
            channel=2,
        )
        statuses = []
        results = []
        failures = []
        worker.status_changed.connect(statuses.append)
        worker.finished.connect(results.append)
        worker.failed.connect(failures.append)

        worker.run()

        controller.fn_run.assert_called_once()
        self.assertEqual(controller.fn_run.call_args.kwargs["log_file"], "demo.asc")
        self.assertEqual(controller.fn_run.call_args.kwargs["channel"], 2)
        self.assertEqual(statuses, ["Reading log..."])
        self.assertEqual(results, [{"transactions": []}])
        self.assertEqual(failures, [])

    def test_worker_emits_failed_message(self):
        controller = Mock()
        controller.fn_run.side_effect = ValueError("Broken log")
        worker = AnalysisWorker(
            controller=controller,
            log_file="demo.asc",
            vehicle=object(),
            channel=2,
        )
        failures = []
        worker.failed.connect(failures.append)

        worker.run()

        self.assertEqual(failures, ["Broken log"])


if __name__ == "__main__":
    unittest.main()
