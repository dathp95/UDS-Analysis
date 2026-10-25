import json
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace


class DiagnosticImportTests(unittest.TestCase):
    def test_four_synthetic_schemas_and_vin_steps(self):
        from core.diagnostic_sequence_import import import_diag
        root = Path(__file__).parents[1] / 'fixtures' / 'can_interface'
        files = list(root.glob('*.diag'))
        self.assertEqual(len(files), 4)
        for path in files:
            case = import_diag(path)
            self.assertTrue(case.steps)
            self.assertEqual(case.steps[0].request,'22 F1 90')
            self.assertEqual(case.steps[0].comment,'')
            self.assertEqual(case.steps[0].match,'prefix')
        case = import_diag(root / '0002.READ VIN(1).diag')
        self.assertEqual(len(case.steps),16)
        self.assertEqual([x.step for x in case.steps],list(range(1,17)))
        self.assertTrue(all(x.expected_response == '62 F1 90' for x in case.steps))
        self.assertEqual(case.steps[0].ecu,'TEST_ECU_01')

    def test_strict_types_and_no_executable_rule_processing(self):
        from core.diagnostic_sequence_import import import_diag
        from repositories.diagnostic_sequence_repository import DiagnosticSequenceValidationError
        payload = dict(Header={}, TestCaseItem=[dict(ECUObj=dict(ECUName='TEST'), TransMess=' 22 f1 90',
                        ExpectMess=None, Remark=None, DelayTime=100, RepeatTimes=1, TransmitRule={'ignored':'no execution'})])
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path=Path(directory)/'test.diag'
            for key, value in (('DelayTime', True), ('DelayTime', 1.5), ('RepeatTimes',0), ('TransMess','ZZ'), ('Remark',{})):
                invalid=json.loads(json.dumps(payload))
                invalid['TestCaseItem'][0][key]=value
                path.write_text(json.dumps(invalid),encoding='utf-8')
                with self.assertRaises(DiagnosticSequenceValidationError):
                    import_diag(path)
            path.write_text(json.dumps(payload),encoding='utf-8')
            self.assertEqual(import_diag(path).steps[0].expected_response,'')

    def test_safe_native_save_and_source_unchanged(self):
        from repositories.can_sequence_repository import CanSequenceRepository
        from repositories.diagnostic_sequence_repository import DiagnosticSequenceValidationError
        fixture=Path(__file__).parents[1]/'fixtures'/'can_interface'/'204.BCM&CDS&1.diag'
        original=fixture.read_bytes()
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            repo=CanSequenceRepository(directory)
            case=repo.fn_load_sequence(fixture)
            edited=replace(case,steps=[replace(case.steps[0],comment='saved comment')])
            with self.assertRaises(DiagnosticSequenceValidationError):
                repo.fn_save_sequence(edited,fixture)
            path=repo.fn_save_sequence(edited,Path(directory)/'converted.json')
            self.assertEqual(repo.fn_load_sequence(path).steps[0].comment,'saved comment')
            self.assertNotIn('DLLFile',path.read_text(encoding='utf-8'))
        self.assertEqual(fixture.read_bytes(),original)
