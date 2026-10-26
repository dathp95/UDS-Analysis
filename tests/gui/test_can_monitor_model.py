import os
import unittest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import QPersistentModelIndex
from PySide6.QtTest import QAbstractItemModelTester
from PySide6.QtWidgets import QApplication

from gui.widgets.can_interface.can_monitor_model import CanMonitorModel
from tests.services.test_blf_recording_service import raw


class CanMonitorModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])

    def test_incremental_eviction_keeps_selection_identity_and_lazy_values(self):
        model=CanMonitorModel()
        tester=QAbstractItemModelTester(model,QAbstractItemModelTester.FailureReportingMode.Warning)
        records=[raw(i) for i in range(1,21)]
        model.set_frames(records[:10]);saved=QPersistentModelIndex(model.index(5,4))
        resets=[];model.modelReset.connect(lambda:resets.append(True))
        model.set_frames(records[2:12])
        self.assertEqual(saved.row(),3)
        self.assertEqual(saved.data(),'01 02')
        self.assertEqual(model.frames[saved.row()].sequence,6)
        self.assertEqual(resets,[])
        model.set_frames([]);self.assertFalse(saved.isValid())
