import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gui.workers.log_channel_worker import LogChannelWorker


class LogChannelWorkerTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_worker_emits_channels_from_core_reader(self):
        worker = LogChannelWorker("C:/logs/sample.blf")
        emitted = []

        worker.finished.connect(emitted.append)

        with patch(
            "gui.workers.log_channel_worker.get_log_channels",
            return_value=[1, 2],
        ) as get_channels:
            worker.run()

        get_channels.assert_called_once_with("C:/logs/sample.blf")
        self.assertEqual(emitted, [[1, 2]])

    def test_worker_emits_failure_message(self):
        worker = LogChannelWorker("C:/logs/broken.blf")
        emitted = []

        worker.failed.connect(emitted.append)

        with patch(
            "gui.workers.log_channel_worker.get_log_channels",
            side_effect=ValueError("Broken log"),
        ):
            worker.run()

        self.assertEqual(emitted, ["Broken log"])


if __name__ == "__main__":
    unittest.main()
