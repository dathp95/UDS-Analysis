import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import can
from PySide6.QtWidgets import QApplication

from gui.controllers.analysis_controller import AnalysisController
from gui.workers.analysis_worker import AnalysisWorker
from gui.workers.log_channel_worker import LogChannelWorker
from models.ecu import ECU
from models.vehicle import Vehicle


class BlfWorkerErrorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_real_invalid_and_truncated_blf_emit_failed_not_finished(self):
        vehicle = Vehicle(name="Test", ecus=[ECU(name="ECU", request_id="682", response_id="602")])
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
            path = Path(directory) / "invalid.blf"
            with can.BLFWriter(path) as writer:
                writer.on_message_received(can.Message(timestamp=1000, arbitration_id=0x682,
                    channel=0, is_extended_id=False, data=bytes.fromhex("02 10 03 AA AA AA AA AA")))
            truncated = path.read_bytes()[:-5]
            for contents in (b"not a BLF file", truncated):
                path.write_bytes(contents)
                for worker in (LogChannelWorker(str(path)),
                               AnalysisWorker(AnalysisController(), str(path), vehicle, 1)):
                    with self.subTest(worker=type(worker).__name__, length=len(contents)):
                        failures, results = [], []
                        worker.failed.connect(failures.append)
                        worker.finished.connect(results.append)
                        worker.run()
                        self.assertEqual(results, [])
                        self.assertEqual(len(failures), 1)
                        self.assertIn("Invalid or truncated BLF", failures[0])
                        self.assertFalse(path.with_suffix(".asc").exists())
                        self.application.processEvents()


if __name__ == "__main__":
    unittest.main()
