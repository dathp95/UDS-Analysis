import os
import time
import unittest
from threading import Event, Timer, get_ident

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QThread, QTimer
from PySide6.QtWidgets import QApplication

from gui.workers.can_connection_worker import CANConnectionTask, CANConnectionOperation as Operation
from gui.workers.can_discovery_worker import CANDiscoveryTask
from services.can import CANConfig, CANService, CANConnectionState as State
from tests.services.test_can_service import FakeCANBackend


class CANConnectionWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.backend = FakeCANBackend()
        self.service = CANService(self.backend)
        self.task = CANConnectionTask(self.service, self.app)
        self.addCleanup(self.task.deleteLater)
        self.addCleanup(self.task.shutdown)
        self.config = CANConfig("vector", 0, 500000)

    def wait(self, predicate):
        deadline = time.monotonic() + 5
        while predicate() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.001)
        self.assertFalse(predicate())

    def run_operation(self, operation, config=None):
        self.assertTrue(self.task.start(operation, config))
        self.wait(lambda: self.task.running)

    def test_open_close_reconnect_use_one_owner_thread_and_gui_delivery(self):
        native_threads, gui_threads, outcomes = [], [], []
        original_open, original_close = self.backend.fn_open, self.backend.fn_close

        def open_bus(config):
            native_threads.append(get_ident())
            original_open(config)

        def close_bus():
            native_threads.append(get_ident())
            original_close()

        self.backend.fn_open, self.backend.fn_close = open_bus, close_bus
        self.task.completed.connect(lambda op, result: (outcomes.append(result.state), gui_threads.append(QThread.currentThread())))
        for _ in range(2):
            self.run_operation(Operation.CONNECT, self.config)
            self.run_operation(Operation.DISCONNECT)
        self.assertEqual(len(set(native_threads)), 1)
        self.assertNotEqual(native_threads[0], get_ident())
        self.assertTrue(all(thread == self.app.thread() for thread in gui_threads))
        self.assertEqual(outcomes, [State.CONNECTED, State.DISCONNECTED] * 2)

    def test_repeated_discovery_teardown_keeps_results_reliable(self):
        task = CANDiscoveryTask(self.service, self.app)
        self.addCleanup(task.dispose)
        results = []
        task.completed.connect(results.append)
        for _ in range(30):
            task.start()
            self.wait(lambda: task.running)
        self.assertEqual(results, [()] * 30)

    def test_duplicate_and_overlap_rejected_while_gui_heartbeat_runs(self):
        entered, release = Event(), Event()
        original = self.backend.fn_open

        def slow(config):
            entered.set()
            release.wait(3)
            original(config)

        self.backend.fn_open = slow
        self.assertTrue(self.task.start(Operation.CONNECT, self.config))
        try:
            self.assertTrue(entered.wait(2))
            self.assertFalse(self.task.start(Operation.CONNECT, self.config))
            self.assertFalse(self.task.start(Operation.DISCONNECT))
            heartbeat = []
            QTimer.singleShot(0, lambda: heartbeat.append(True))
            self.app.processEvents()
            self.assertEqual(heartbeat, [True])
        finally:
            release.set()
            self.wait(lambda: self.task.running)

    def test_shutdown_during_open_discards_result_and_closes_same_owner(self):
        release, entered = Event(), Event()
        original = self.backend.fn_open
        outcomes = []

        def slow(config):
            entered.set()
            release.wait(3)
            original(config)

        self.backend.fn_open = slow
        self.task.completed.connect(lambda *args: outcomes.append(args))
        self.task.failed.connect(lambda *args: outcomes.append(args))
        self.task.start(Operation.CONNECT, self.config)
        self.assertTrue(entered.wait(2))
        self.task.dispose()
        release.set()
        self.wait(lambda: self.task.alive)
        self.assertEqual(outcomes, [])
        self.assertEqual(self.service.snapshot.state, State.DISCONNECTED)
        self.assertEqual(self.backend.close_count, 1)

    def test_shutdown_pumps_events_while_slow_disconnect_finishes(self):
        self.run_operation(Operation.CONNECT, self.config)
        release = Event()
        original = self.backend.fn_close

        def slow():
            release.wait(3)
            original()

        self.backend.fn_close = slow
        heartbeat = []
        QTimer.singleShot(0, lambda: heartbeat.append(True))
        timer = Timer(0.05, release.set)
        timer.start()
        try:
            self.task.shutdown()
        finally:
            release.set()
            timer.join()
        self.assertFalse(self.task.alive)
        self.assertEqual(heartbeat, [True])
        self.assertEqual(self.service.snapshot.state, State.DISCONNECTED)

    def test_one_terminal_error_and_no_stale_token_delivery(self):
        errors, completions, finished = [], [], []
        self.task.failed.connect(lambda *args: errors.append(args))
        self.task.completed.connect(lambda *args: completions.append(args))
        self.task.finished.connect(finished.append)
        self.run_operation(Operation.CONNECT, CANConfig("vector", -1, 500000))
        self.assertEqual(len(errors), 1)
        self.assertEqual(finished, [Operation.CONNECT])
        self.assertEqual(completions, [])
        self.task._complete(0, Operation.CONNECT, self.service.snapshot)
        self.assertEqual(completions, [])

