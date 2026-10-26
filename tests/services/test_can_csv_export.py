import csv
from pathlib import Path
import tempfile
import unittest

from services.can.can_csv_export import export_retained_csv,HEADERS
from tests.services.test_blf_recording_service import raw


class CanCsvTests(unittest.TestCase):
    def test_bom_headers_and_retained_frame_values_no_overwrite(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path=Path(directory)/'retained.csv'
            self.assertEqual(export_retained_csv(path,[raw(1),raw(2,channel=1)]),2)
            self.assertTrue(path.read_bytes().startswith(b'\xef\xbb\xbf'))
            with path.open(encoding='utf-8-sig',newline='') as handle: rows=list(csv.reader(handle))
            self.assertEqual(rows[0],list(HEADERS))
            self.assertEqual(rows[1][2:8],['RX','0','760','0','2','01 02'])
            self.assertEqual(rows[2][3],'1')
            with self.assertRaises(FileExistsError): export_retained_csv(path,[])
