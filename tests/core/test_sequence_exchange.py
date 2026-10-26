import unittest
from core.diagnostic_sequence import DiagnosticStep


class SequenceExchangeTests(unittest.TestCase):
    def test_tsv_round_trip_quoted_comment_and_informational_result(self):
        from core.sequence_exchange import export_sequence_text, parse_sequence_text, HEADERS
        step=DiagnosticStep(1,'VIN','BCM','22 F1 90',comment=' tabs\tand\nlines ')
        text=export_sequence_text([step],['Passed'])
        self.assertEqual(text.splitlines()[0],'\t'.join(HEADERS))
        result=parse_sequence_text(text,ecu_names={'BCM'})
        self.assertEqual(result.steps[0],step)
        self.assertTrue(any('Results' in note for note in result.diagnostics))
        self.assertFalse(hasattr(result.steps[0],'result'))

    def test_validation_reports_source_line_and_never_returns_partial_rows(self):
        from core.sequence_exchange import export_sequence_text,parse_sequence_text
        valid=DiagnosticStep(1,'VIN','BCM','22 F1 90')
        text=export_sequence_text([valid,DiagnosticStep(2,'VIN','EPS','GG',repeat=0)])
        with self.assertRaisesRegex(ValueError,'Row 3'): parse_sequence_text(text)
        with self.assertRaises(ValueError): parse_sequence_text(text+'\nwrong\tlength')

    def test_csv_unknown_blank_and_missing_vehicle(self):
        import csv,io
        from core.sequence_exchange import parse_sequence_text,HEADERS
        out=io.StringIO();writer=csv.writer(out)
        writer.writerow(HEADERS);writer.writerow([1,'name','unknown<>','22 F1 90','',1,'','','a,b'])
        result=parse_sequence_text(out.getvalue(),ecu_names={'BCM'})
        self.assertEqual(result.steps[0].ecu,'unknown<>')
        self.assertTrue(any('unknown<>' in note for note in result.diagnostics))
        self.assertEqual(parse_sequence_text(out.getvalue()).diagnostics,())
