import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from core.diagnostic_sequence import (
    DiagnosticExecutionSettings,
    DiagnosticStep,
    DiagnosticTestCase,
)
from gui.widgets.diagnostic.diagnostic_sequence_table import DiagnosticSequenceTable


class DiagnosticSequenceTableTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_load_sequence_displays_execution_settings_and_steps(self):
        widget = DiagnosticSequenceTable()
        self.addCleanup(widget.deleteLater)
        test_case = self._test_case()

        widget.fn_load_sequence(test_case)

        self.assertEqual(widget.txt_loop.text(), "3")
        self.assertEqual(widget.txt_command_delay.text(), "250")
        self.assertEqual(widget.table.rowCount(), 1)
        self.assertEqual(widget.table.item(0, widget.COL_INDEX).text(), "1")
        self.assertEqual(widget.table.item(0, widget.COL_STEP).text(), "1")
        self.assertEqual(widget.table.item(0, widget.COL_SEQUENCE_NAME).text(), "Read VIN")
        self.assertEqual(widget.table.cellWidget(0, widget.COL_ECU).currentText(), "ACU")
        self.assertEqual(widget.table.item(0, widget.COL_REQUEST).text(), "22 F1 90")
        self.assertEqual(widget.table.item(0, widget.COL_DELAY).text(), "")
        self.assertEqual(widget.table.item(0, widget.COL_REPEAT).text(), "2")
        self.assertEqual(widget.table.item(0, widget.COL_EXPECTED).text(), "62 F1 90")
        self.assertEqual(widget.table.item(0, widget.COL_RECEIVE).text(), "")
        self.assertEqual(widget.table.item(0, widget.COL_RESULT).text(), "")

    def test_old_sequence_without_execution_uses_default_inputs(self):
        widget = DiagnosticSequenceTable()
        self.addCleanup(widget.deleteLater)
        test_case = DiagnosticTestCase(
            schema_version=1,
            name="READ VIN",
            description="",
            enabled=True,
            steps=[],
        )

        widget.fn_load_sequence(test_case)

        self.assertEqual(widget.txt_loop.text(), "1")
        self.assertEqual(widget.txt_command_delay.text(), "100")

    def test_editing_loop_and_command_delay_updates_model(self):
        widget = DiagnosticSequenceTable()
        self.addCleanup(widget.deleteLater)
        modified = []
        widget.sequence_modified.connect(modified.append)
        widget.fn_load_sequence(self._test_case())

        widget.txt_loop.setText("4")
        widget.txt_loop.editingFinished.emit()
        widget.txt_command_delay.setText("500")
        widget.txt_command_delay.editingFinished.emit()

        current = widget.fn_current_sequence()
        self.assertEqual(current.execution.loop, 4)
        self.assertEqual(current.execution.command_delay_ms, 500)
        self.assertTrue(widget.fn_is_dirty())
        self.assertGreaterEqual(len(modified), 2)

    def test_editing_request_normalizes_hex_and_updates_model(self):
        widget = DiagnosticSequenceTable()
        self.addCleanup(widget.deleteLater)
        widget.fn_load_sequence(self._test_case())

        item = widget.table.item(0, widget.COL_REQUEST)
        item.setText("22 f3 90")

        self.assertEqual(widget.fn_current_sequence().steps[0].request, "22 F3 90")
        self.assertEqual(widget.table.item(0, widget.COL_REQUEST).text(), "22 F3 90")

    def test_invalid_request_restores_previous_value_without_crash(self):
        widget = DiagnosticSequenceTable()
        self.addCleanup(widget.deleteLater)
        widget.fn_load_sequence(self._test_case())

        item = widget.table.item(0, widget.COL_REQUEST)
        item.setText("22 F1 ZZ")

        self.assertEqual(widget.fn_current_sequence().steps[0].request, "22 F1 90")
        self.assertEqual(widget.table.item(0, widget.COL_REQUEST).text(), "22 F1 90")

    def test_blank_delay_remains_none_and_repeat_is_independent_from_loop(self):
        widget = DiagnosticSequenceTable()
        self.addCleanup(widget.deleteLater)
        widget.fn_load_sequence(self._test_case())

        widget.table.item(0, widget.COL_DELAY).setText("")
        widget.table.item(0, widget.COL_REPEAT).setText("5")
        widget.txt_loop.setText("2")
        widget.txt_loop.editingFinished.emit()

        current = widget.fn_current_sequence()
        self.assertIsNone(current.steps[0].delay_ms)
        self.assertEqual(current.steps[0].repeat, 5)
        self.assertEqual(current.execution.loop, 2)

    def test_receive_and_result_are_read_only(self):
        widget = DiagnosticSequenceTable()
        self.addCleanup(widget.deleteLater)
        widget.fn_load_sequence(self._test_case())

        receive_flags = widget.table.item(0, widget.COL_RECEIVE).flags()
        result_flags = widget.table.item(0, widget.COL_RESULT).flags()

        self.assertFalse(receive_flags & Qt.ItemIsEditable)
        self.assertFalse(result_flags & Qt.ItemIsEditable)

    def test_switching_sequence_loads_its_own_settings(self):
        widget = DiagnosticSequenceTable()
        self.addCleanup(widget.deleteLater)
        widget.fn_load_sequence(self._test_case(loop=3, command_delay_ms=250))

        widget.fn_load_sequence(self._test_case(loop=1, command_delay_ms=100, name="READ CDS"))

        self.assertEqual(widget.txt_loop.text(), "1")
        self.assertEqual(widget.txt_command_delay.text(), "100")
        self.assertEqual(widget.table.item(0, widget.COL_SEQUENCE_NAME).text(), "Read VIN")
        self.assertFalse(widget.fn_is_dirty())

    def test_add_step_appends_editable_placeholder_step(self):
        widget = DiagnosticSequenceTable()
        self.addCleanup(widget.deleteLater)
        widget.fn_load_sequence(self._test_case())

        widget.fn_add_step()

        current = widget.fn_current_sequence()
        self.assertEqual(widget.table.rowCount(), 2)
        self.assertEqual(current.steps[1].step, 2)
        self.assertIsNone(current.steps[1].delay_ms)
        self.assertTrue(widget.fn_is_dirty())

    @staticmethod
    def _test_case(loop=3, command_delay_ms=250, name="READ VIN"):
        return DiagnosticTestCase(
            schema_version=1,
            name=name,
            description="Read VIN from selected ECUs",
            enabled=True,
            execution=DiagnosticExecutionSettings(
                loop=loop,
                command_delay_ms=command_delay_ms,
            ),
            steps=[
                DiagnosticStep(
                    step=1,
                    sequence_name="Read VIN",
                    ecu="ACU",
                    request="22 F1 90",
                    delay_ms=None,
                    repeat=2,
                    expected_response="62 F1 90",
                    match="prefix",
                    comment="",
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
