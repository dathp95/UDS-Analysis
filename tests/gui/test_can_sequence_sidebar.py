import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt, QModelIndex, QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from core.diagnostic_sequence import DiagnosticStep, DiagnosticTestCase
from repositories.diagnostic_sequence_repository import DiagnosticSequenceRepository


class CanSequenceSidebarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_search_checks_order_and_explicit_persistence(self):
        from repositories.can_interface_ui_store import CanInterfaceUiStore
        from gui.widgets.can_interface.sequence_sidebar import CanSequenceSidebar
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            root = Path(directory)
            repository = DiagnosticSequenceRepository(root / 'sequences')
            for name in ('204.BCM', '0002.VIN', '0001.READ', '9302.MHU'):
                repository.fn_save_sequence(DiagnosticTestCase(1, name, '', True, [DiagnosticStep(1, name, 'TEST', '22 F1 90')]), repository.root / f'{name}.json')
            store = CanInterfaceUiStore(root / 'ui.json')
            sidebar = CanSequenceSidebar(repository, store)
            self.addCleanup(sidebar.deleteLater)
            original = sidebar.source_ids()
            self.assertEqual([Path(x).stem for x in original], ['0001.READ','0002.VIN','204.BCM','9302.MHU'])
            self.assertFalse(sidebar.btn_save_order.isEnabled())
            sidebar.list_sequences.item(3).setCheckState(Qt.Checked)
            sidebar.edit_search.setText('vin')
            sidebar.chk_select_all.setChecked(True)
            self.assertEqual(set(sidebar.checked_ids()), {original[1], original[3]})
            self.assertFalse(sidebar.reorder(tuple(reversed(original))))
            sidebar.edit_search.clear()
            self.assertTrue(sidebar.reorder(tuple(reversed(original))))
            self.assertTrue(sidebar.btn_save_order.isEnabled())
            store.save_selection(original[1])
            self.assertEqual(store.load().order, ())
            sidebar.btn_save_order.click()
            self.assertEqual(store.load().order, tuple(reversed(original)))
            self.assertFalse(sidebar.btn_save_order.isEnabled())
            reopened = CanSequenceSidebar(repository, store)
            self.addCleanup(reopened.deleteLater)
            self.assertEqual(reopened.source_ids(), tuple(reversed(original)))
            sidebar.reorder(original)
            sidebar.fn_refresh_sequences()
            self.assertEqual(sidebar.source_ids(), original)
            self.assertTrue(sidebar.btn_save_order.isEnabled())

    def test_real_checkbox_click_does_not_preview_and_native_move_marks_dirty(self):
        from gui.widgets.can_interface.sequence_sidebar import CanSequenceSidebar
        from repositories.can_interface_ui_store import CanInterfaceUiStore
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            root=Path(directory)
            repo=DiagnosticSequenceRepository(root/'seq')
            for i in (1,2):
                repo.fn_save_sequence(DiagnosticTestCase(1,f'Case {i}','',True,[]),repo.root/f'{i}.json')
            sidebar=CanSequenceSidebar(repo,CanInterfaceUiStore(root/'prefs'))
            self.addCleanup(sidebar.deleteLater)
            sidebar.resize(280,500)
            sidebar.show()
            self.app.processEvents()
            opened=[]
            sidebar.sequence_open_requested.connect(opened.append)
            item=sidebar.list_sequences.item(0)
            rect=sidebar.list_sequences.visualItemRect(item)
            QTest.mouseClick(sidebar.list_sequences.viewport(),Qt.LeftButton,pos=QPoint(rect.left()+10,rect.center().y()))
            self.assertEqual(item.checkState(),Qt.Checked)
            self.assertEqual(opened,[])
            QTest.mouseClick(sidebar.list_sequences.viewport(),Qt.LeftButton,pos=QPoint(rect.left()+70,rect.center().y()))
            self.assertEqual(opened,[item.data(sidebar.ITEM_PATH_ROLE)])
            original=sidebar.source_ids()
            self.assertTrue(sidebar.list_sequences.model().moveRows(QModelIndex(),0,1,QModelIndex(),2))
            self.assertEqual(sidebar.source_ids(),tuple(reversed(original)))
            self.assertTrue(sidebar.btn_save_order.isEnabled())
