import json
import tempfile
import unittest
from pathlib import Path

from core.diagnostic_sequence import (
    DiagnosticExecutionSettings,
    DiagnosticStep,
    DiagnosticTestCase,
)
from repositories.diagnostic_sequence_repository import (
    DiagnosticSequenceValidationError,
    DiagnosticSequenceRepository,
)


class DiagnosticSequenceRepositoryTests(unittest.TestCase):

    def test_load_valid_read_vin_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sequence_file = Path(tmpdir) / "0002_READ_VIN.json"
            sequence_file.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "name": "READ VIN",
                        "description": "Read VIN from selected ECUs",
                        "enabled": True,
                        "steps": [
                            {
                                "step": 1,
                                "sequence_name": "Read VIN",
                                "ecu": "ACU",
                                "request": "22 f1 90",
                                "delay_ms": 100,
                                "repeat": 1,
                                "expected_response": "62 f1 90",
                                "match": "prefix",
                                "comment": "",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            repository = DiagnosticSequenceRepository(root=tmpdir)

            test_case = repository.fn_load_sequence(sequence_file)

            self.assertIsInstance(test_case, DiagnosticTestCase)
            self.assertEqual(test_case.name, "READ VIN")
            self.assertEqual(test_case.steps[0].request, "22 F1 90")
            self.assertEqual(test_case.steps[0].expected_response, "62 F1 90")

    def test_save_sequence_round_trip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repository = DiagnosticSequenceRepository(root=tmpdir)
            sequence_file = Path(tmpdir) / "0002_READ_VIN.json"
            test_case = DiagnosticTestCase(
                schema_version=1,
                name="READ VIN",
                description="Read VIN from selected ECUs",
                enabled=True,
                steps=[
                    DiagnosticStep(
                        step=1,
                        sequence_name="Read VIN",
                        ecu="ACU",
                        request="22 f1 90",
                        expected_response="62 f1 90",
                    ),
                ],
            )

            repository.fn_save_sequence(test_case, sequence_file)
            loaded = repository.fn_load_sequence(sequence_file)

            self.assertEqual(loaded.steps[0].request, "22 F1 90")
            self.assertEqual(loaded.steps[0].expected_response, "62 F1 90")
            payload = json.loads(sequence_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["steps"][0]["request"], "22 F1 90")


    def test_load_sequence_with_execution_settings_and_null_step_delay(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sequence_file = Path(tmpdir) / "0002_READ_VIN.json"
            sequence_file.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "name": "READ VIN",
                        "description": "Read VIN from selected ECUs",
                        "enabled": True,
                        "execution": {
                            "loop": 3,
                            "command_delay_ms": 250,
                        },
                        "steps": [
                            {
                                "step": 1,
                                "sequence_name": "Read VIN",
                                "ecu": "ACU",
                                "request": "22 f1 90",
                                "delay_ms": None,
                                "repeat": 2,
                                "expected_response": "62 f1 90",
                                "match": "prefix",
                                "comment": "",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            repository = DiagnosticSequenceRepository(root=tmpdir)

            test_case = repository.fn_load_sequence(sequence_file)

            self.assertEqual(test_case.execution.loop, 3)
            self.assertEqual(test_case.execution.command_delay_ms, 250)
            self.assertIsNone(test_case.steps[0].delay_ms)
            self.assertEqual(test_case.steps[0].repeat, 2)

    def test_old_sequence_without_execution_uses_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sequence_file = Path(tmpdir) / "0002_READ_VIN.json"
            sequence_file.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "name": "READ VIN",
                        "description": "",
                        "enabled": True,
                        "steps": [
                            {
                                "step": 1,
                                "sequence_name": "Read VIN",
                                "ecu": "ACU",
                                "request": "22 F1 90",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            repository = DiagnosticSequenceRepository(root=tmpdir)

            test_case = repository.fn_load_sequence(sequence_file)

            self.assertEqual(test_case.execution.loop, 1)
            self.assertEqual(test_case.execution.command_delay_ms, 100)

    def test_save_sequence_writes_execution_settings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repository = DiagnosticSequenceRepository(root=tmpdir)
            sequence_file = Path(tmpdir) / "0002_READ_VIN.json"
            test_case = DiagnosticTestCase(
                schema_version=1,
                name="READ VIN",
                description="",
                enabled=True,
                execution=DiagnosticExecutionSettings(
                    loop=4,
                    command_delay_ms=500,
                ),
                steps=[
                    DiagnosticStep(
                        step=1,
                        sequence_name="Read VIN",
                        ecu="ACU",
                        request="22 F1 90",
                        delay_ms=None,
                    ),
                ],
            )

            repository.fn_save_sequence(test_case, sequence_file)

            payload = json.loads(sequence_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["execution"]["loop"], 4)
            self.assertEqual(payload["execution"]["command_delay_ms"], 500)
            self.assertIsNone(payload["steps"][0]["delay_ms"])

    def test_invalid_execution_settings_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sequence_file = Path(tmpdir) / "0002_READ_VIN.json"
            sequence_file.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "name": "READ VIN",
                        "description": "",
                        "enabled": True,
                        "execution": {
                            "loop": 0,
                            "command_delay_ms": 100,
                        },
                        "steps": [],
                    }
                ),
                encoding="utf-8",
            )
            repository = DiagnosticSequenceRepository(root=tmpdir)

            with self.assertRaisesRegex(
                DiagnosticSequenceValidationError,
                "loop",
            ):
                repository.fn_load_sequence(sequence_file)

    def test_invalid_hex_is_rejected_safely(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sequence_file = Path(tmpdir) / "0002_READ_VIN.json"
            sequence_file.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "name": "READ VIN",
                        "description": "",
                        "enabled": True,
                        "steps": [
                            {
                                "step": 1,
                                "sequence_name": "Read VIN",
                                "ecu": "ACU",
                                "request": "22 F1 ZZ",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            repository = DiagnosticSequenceRepository(root=tmpdir)

            with self.assertRaisesRegex(
                DiagnosticSequenceValidationError,
                "request",
            ):
                repository.fn_load_sequence(sequence_file)

    def test_missing_required_field_returns_clear_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sequence_file = Path(tmpdir) / "0002_READ_VIN.json"
            sequence_file.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "description": "",
                        "enabled": True,
                        "steps": [],
                    }
                ),
                encoding="utf-8",
            )
            repository = DiagnosticSequenceRepository(root=tmpdir)

            with self.assertRaisesRegex(
                DiagnosticSequenceValidationError,
                "name",
            ):
                repository.fn_load_sequence(sequence_file)

    def test_invalid_json_returns_clear_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sequence_file = Path(tmpdir) / "broken.json"
            sequence_file.write_text("{broken", encoding="utf-8")
            repository = DiagnosticSequenceRepository(root=tmpdir)

            with self.assertRaisesRegex(
                DiagnosticSequenceValidationError,
                "Invalid JSON",
            ):
                repository.fn_load_sequence(sequence_file)

    def test_list_sequences_returns_sorted_json_files_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "0010_ExtendedSession.json").write_text(
                "{}",
                encoding="utf-8",
            )
            (root / "0002_READ_VIN.json").write_text(
                "{}",
                encoding="utf-8",
            )
            (root / "notes.txt").write_text(
                "",
                encoding="utf-8",
            )
            repository = DiagnosticSequenceRepository(root=root)

            sequences = repository.fn_list_sequences()

            self.assertEqual(
                [path.name for path in sequences],
                [
                    "0002_READ_VIN.json",
                    "0010_ExtendedSession.json",
                ],
            )


if __name__ == "__main__":
    unittest.main()
