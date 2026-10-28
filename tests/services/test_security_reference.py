import unittest

from services.can.security_reference import extract_reference_rows


HEADER = ('ECU', 'Time', 'Request', 'Response', 'RT (ms)', 'Status')


def row(time, request, response, ecu='BCM', rt=1):
    return (ecu, time, request, response, rt, 'POSITIVE')


class SecurityReferenceTests(unittest.TestCase):
    def extract(self, *rows):
        return extract_reference_rows([('Title',), HEADER, *rows])

    def test_full_same_ecu_pairs_and_levels_without_fixed_length(self):
        result = self.extract(row(1, '10 03', '50 03'),
                              row(2, '27 01', '67 01 AA BB'),
                              row(2.1, '27 02 11 22 33', '67 02'),
                              row(3, '27 03', '67 03 44'),
                              row(3.1, '27 04 55', '67 04'))
        self.assertEqual([(v.subfunction, len(v.seed), len(v.key)) for v in result.vectors],
                         [(1, 2, 3), (3, 1, 1)])
        self.assertNotIn('AA BB', repr(result))
        self.assertNotIn('112233', repr(result.vectors[0]))

    def test_other_ecu_does_not_consume_seed(self):
        result = self.extract(row(1, '27 01', '67 01 AA'),
                              row(1.1, '22 F1 90', '62 F1 90', ecu='EPS'),
                              row(1.2, '27 02 11', '67 02'))
        self.assertEqual(len(result.vectors), 1)

    def test_session_change_competing_seed_and_negative_never_reuse(self):
        for middle in (row(1.1, '10 03', '50 03'), row(1.1, '22 F1 90', '62 F1 90'),
                       row(1.1, '27 01', '7F 27 33')):
            with self.subTest(middle=middle[2]):
                result = self.extract(row(1, '27 01', '67 01 AA'), middle,
                                      row(1.2, '27 02 11', '67 02'))
                self.assertEqual(result.vectors, ())

    def test_bad_echo_empty_seed_and_key_ack_with_data_are_not_success(self):
        for response in ('67 01', '67 02 AA', '7F 27 78', '7F 27 35', 'not hex'):
            result = self.extract(row(1, '27 01', response), row(2, '27 02 11', '67 02'))
            self.assertEqual(result.vectors, ())
        result = self.extract(row(1, '27 01', '67 01 AA'), row(2, '27 02 11', '67 02 00'))
        self.assertEqual(result.vectors, ())

    def test_chronology_uses_response_completion_and_seed_is_single_use(self):
        result = self.extract(row(1, '27 01', '67 01 AA', rt=500),
                              row(1.1, '27 02 11', '67 02'))
        self.assertEqual(result.vectors, ())
        result = self.extract(row(1, '27 01', '67 01 AA'),
                              row(2, '27 02 11', '67 02'), row(3, '27 02 11', '67 02'))
        self.assertEqual(len(result.vectors), 1)

    def test_missing_headers_and_nonchronological_input_fail_closed(self):
        with self.assertRaises(ValueError): extract_reference_rows([('unexpected',)])
        result = self.extract(row(2, '27 01', '67 01 AA'), row(1, '27 02 11', '67 02'))
        self.assertEqual(result.vectors, ())
