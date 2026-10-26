import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QFileDialog
from models.ecu import ECU
from gui.widgets.vehicle_manager.ecu_resource import ECUResourceWidget
from tests.dll_fixture import pe_dll


class EcuDllResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path.cwd());self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'example.dll';self.path.write_bytes(pe_dll())
        self.widget=ECUResourceWidget();self.addCleanup(self.widget.deleteLater)
        self.ecu=ECU('BCM','681','601',resources={'dll':'','dbc':'original.dbc','custom':'keep'})
        self.widget.fn_set_ecu(self.ecu)

    def test_browse_cancel_valid_path_and_draft_are_isolated(self):
        with patch.object(QFileDialog,'getOpenFileName',return_value=(str(self.path),'')):
            self.widget.btn_dll.click()
        self.assertEqual(self.widget.txt_dll.text(),str(self.path))
        self.assertEqual(self.widget.txt_dll.toolTip(),str(self.path))
        self.assertEqual(self.ecu.resources['dll'],'')
        draft=self.widget.fn_get_ecu(self.ecu)
        self.assertIsNot(draft,self.ecu)
        self.assertEqual(draft.resources['dll'],str(self.path))
        self.assertEqual(draft.resources['custom'],'keep')
        self.assertEqual(draft.resources['dbc'],'original.dbc')
        with patch.object(QFileDialog,'getOpenFileName',return_value=('','')): self.widget.btn_dll.click()
        self.assertEqual(self.widget.txt_dll.text(),str(self.path))
        self.widget.fn_set_ecu(ECU('EPS'))
        self.assertEqual(self.widget.txt_dll.text(),'')
        self.assertEqual(self.ecu.resources['dll'],'')

    def test_invalid_browse_and_manual_edit_fail_without_mutation(self):
        bad=self.path.with_name('broken.dll');bad.write_bytes(b'bad PE')
        with patch.object(QFileDialog,'getOpenFileName',return_value=(str(bad),'')): self.widget.btn_dll.click()
        self.assertEqual(self.widget.txt_dll.text(),'')
        self.assertIn('truncated',self.widget.lbl_dll_status.text().lower())
        self.widget.txt_dll.setText(str(bad))
        with self.assertRaises(ValueError): self.widget.fn_get_ecu(self.ecu)
        self.assertEqual(self.ecu.resources['dll'],'')

    def test_missing_saved_resource_warns_but_does_not_block_unrelated_save(self):
        self.ecu.resources['dll']=str(self.path.with_name('moved.dll'))
        self.widget.fn_set_ecu(self.ecu)
        self.assertIn('missing',self.widget.lbl_dll_status.text().lower())
        self.widget.txt_odx.setText('changed.odx')
        draft=self.widget.fn_get_ecu(self.ecu)
        self.assertEqual(draft.resources['dll'],self.ecu.resources['dll'])
        self.assertEqual(draft.resources['odx'],'changed.odx')

    def test_null_and_missing_resource_mappings_are_compatible(self):
        for resources in (None,{}):
            ecu=ECU('LEGACY',resources=resources)
            self.widget.fn_set_ecu(ecu)
            self.assertEqual(self.widget.txt_dll.text(),'')
            self.assertEqual(self.widget.fn_get_ecu(ecu).resources['dll'],'')
