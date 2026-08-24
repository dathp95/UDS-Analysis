import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from gui.widgets.diagnostic.diagnostic_sequence_list import DiagnosticSequenceList
from repositories.diagnostic_sequence_repository import DiagnosticSequenceRepository


class DiagnosticSequenceListTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_displays_valid_sequences_in_numeric_order(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_sequence(tmpdir, "0010_ExtendedSession.json", "ExtendedSession")
            self._write_sequence(tmpdir, "0002_READ_VIN.json", "READ VIN")
            self._write_sequence(tmpdir, "0200_BCM_Basic_DID.json", "BCM Basic DID")

            widget = self._create_widget(tmpdir)
            self.addCleanup(widget.deleteLater)

            self.assertEqual(
                self._item_texts(widget),
                [
                    "0002. READ VIN",
                    "0010. ExtendedSession",
                    "0200. BCM Basic DID",
                ],
            )

    def test_select_all_checks_all_sequences(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_sequence(tmpdir, "0001_READ_CDS.json", "READ CDS")
            self._write_sequence(tmpdir, "0002_READ_VIN.json", "READ VIN")
            widget = self._create_widget(tmpdir)
            self.addCleanup(widget.deleteLater)

            widget.chk_select_all.setChecked(True)

            self.assertEqual(
                [item.checkState() for item in self._items(widget)],
                [Qt.Checked, Qt.Checked],
            )
            self.assertEqual(
                [case.name for case in widget.fn_selected_sequences()],
                ["READ CDS", "READ VIN"],
            )

    def test_unchecking_one_item_clears_select_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_sequence(tmpdir, "0001_READ_CDS.json", "READ CDS")
            self._write_sequence(tmpdir, "0002_READ_VIN.json", "READ VIN")
            widget = self._create_widget(tmpdir)
            self.addCleanup(widget.deleteLater)

            widget.chk_select_all.setChecked(True)
            widget.list_sequences.item(0).setCheckState(Qt.Unchecked)

            self.assertFalse(widget.chk_select_all.isChecked())

    def test_selecting_all_manually_checks_select_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_sequence(tmpdir, "0001_READ_CDS.json", "READ CDS")
            self._write_sequence(tmpdir, "0002_READ_VIN.json", "READ VIN")
            widget = self._create_widget(tmpdir)
            self.addCleanup(widget.deleteLater)

            widget.list_sequences.item(0).setCheckState(Qt.Checked)
            widget.list_sequences.item(1).setCheckState(Qt.Checked)

            self.assertTrue(widget.chk_select_all.isChecked())

    def test_clicking_sequence_emits_model_without_changing_checkbox_selection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_sequence(tmpdir, "0002_READ_VIN.json", "READ VIN")
            widget = self._create_widget(tmpdir)
            self.addCleanup(widget.deleteLater)
            emitted = []
            widget.sequence_selected.connect(emitted.append)

            item = widget.list_sequences.item(0)
            widget.list_sequences.itemClicked.emit(item)

            self.assertEqual(emitted[0].name, "READ VIN")
            self.assertEqual(item.checkState(), Qt.Unchecked)

    def test_invalid_json_does_not_crash_and_keeps_valid_sequences(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_sequence(tmpdir, "0002_READ_VIN.json", "READ VIN")
            Path(tmpdir, "0001_BROKEN.json").write_text(
                "{broken",
                encoding="utf-8",
            )

            widget = self._create_widget(tmpdir)
            self.addCleanup(widget.deleteLater)

            self.assertEqual(self._item_texts(widget), ["0002. READ VIN"])
            self.assertIn("0001_BROKEN.json", widget.lbl_error.text())

    def test_empty_folder_shows_empty_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            widget = self._create_widget(tmpdir)
            self.addCleanup(widget.deleteLater)

            self.assertEqual(widget.list_sequences.count(), 0)
            self.assertEqual(widget.lbl_empty.text(), "No diagnostic sequences found.")
            self.assertFalse(widget.lbl_empty.isHidden())

    def test_refresh_detects_new_json_and_preserves_selection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_sequence(tmpdir, "0001_READ_CDS.json", "READ CDS")
            widget = self._create_widget(tmpdir)
            self.addCleanup(widget.deleteLater)
            widget.list_sequences.item(0).setCheckState(Qt.Checked)

            self._write_sequence(tmpdir, "0002_READ_VIN.json", "READ VIN")
            widget.fn_refresh_sequences()

            self.assertEqual(
                self._item_texts(widget),
                [
                    "0001. READ CDS",
                    "0002. READ VIN",
                ],
            )
            self.assertEqual(widget.list_sequences.item(0).checkState(), Qt.Checked)
            self.assertEqual(widget.list_sequences.item(1).checkState(), Qt.Unchecked)

    def _create_widget(self, root):
        return DiagnosticSequenceList(
            repository=DiagnosticSequenceRepository(root=root)
        )

    @staticmethod
    def _write_sequence(root, filename, name):
        Path(root, filename).write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "name": name,
                    "description": "",
                    "enabled": True,
                    "steps": [
                        {
                            "step": 1,
                            "sequence_name": name,
                            "ecu": "ACU",
                            "request": "22 F1 90",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _items(widget):
        return [
            widget.list_sequences.item(index)
            for index in range(widget.list_sequences.count())
        ]

    def _item_texts(self, widget):
        return [
            item.text()
            for item in self._items(widget)
        ]


if __name__ == "__main__":
    unittest.main()
