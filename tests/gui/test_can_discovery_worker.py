import os
import time
import unittest
from threading import Event
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication

from gui.workers.can_discovery_worker import CANDiscoveryTask, CANDiscoveryWorker
from services.can import CANDiscoveryError, VectorDriverUnavailableError


class CANDiscoveryWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def wait(self, task):
        deadline = time.monotonic() + 5
        while task.running and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.001)
        self.assertFalse(task.running)

    def test_success_emitted_on_gui_only_after_thread_stops(self):
        threads, completions = [], []

        def detect():
            threads.append(QThread.currentThread())
            return ()

        task = CANDiscoveryTask(SimpleNamespace(fn_refresh=detect), self.app)
        self.addCleanup(task.deleteLater)
        task.completed.connect(lambda result: completions.append((result, task.running, QThread.currentThread())))
        task.start()
        task.start()
        self.wait(task)
        self.assertEqual(len(threads), 1)
        self.assertNotEqual(threads[0], self.app.thread())
        self.assertEqual(completions, [((), False, self.app.thread())])
        self.assertIsNone(task._worker)

    def test_known_error_is_preserved_and_finished_is_emitted(self):
        error = VectorDriverUnavailableError("Vector XL Driver is unavailable.")

        def fail():
            raise error

        worker = CANDiscoveryWorker(SimpleNamespace(fn_refresh=fail))
        finished = []
        worker.finished.connect(lambda: finished.append(True))
        worker.run()
        self.assertEqual(finished, [True])
        self.assertEqual(worker.outcome, (False, error))
        worker.deleteLater()

    def test_unexpected_failure_has_concise_message_and_technical_cause(self):
        def fail():
            raise RuntimeError("technical SDK detail")

        worker = CANDiscoveryWorker(SimpleNamespace(fn_refresh=fail))
        with self.assertLogs("gui.workers.can_discovery_worker", level="ERROR"):
            worker.run()
        success, error = worker.outcome
        self.assertFalse(success)
        self.assertIsInstance(error, CANDiscoveryError)
        self.assertIsInstance(error.__cause__, RuntimeError)
        self.assertNotIn("technical SDK detail", str(error))
        worker.deleteLater()

    def test_shutdown_waits_for_native_work_and_discards_pending_result(self):
        entered, release = Event(), Event()

        def detect():
            entered.set()
            release.wait(5)
            return ()

        task = CANDiscoveryTask(SimpleNamespace(fn_refresh=detect), self.app)
        completions, errors = [], []
        task.completed.connect(completions.append)
        task.failed.connect(errors.append)
        task.start()
        self.assertTrue(entered.wait(2))
        release.set()
        task.shutdown()
        self.wait(task)
        self.assertEqual(completions, [])
        self.assertEqual(errors, [])
