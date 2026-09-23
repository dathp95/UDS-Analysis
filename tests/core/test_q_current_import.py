import sqlite3
import tempfile
from contextlib import closing
import unittest
from pathlib import Path
from unittest.mock import patch

from core.q_current_import import import_q_current_file


class QCurrentImportTests(unittest.TestCase):

    def test_import_csv_writes_sqlite_database_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source_file = root / "sample.csv"
            source_file.write_text(
                "time,current_ma\n0,12.5\n1,13.75\n",
                encoding="utf-8",
            )
            output_root = root / "Report Qcurrent"

            with patch("core.q_current_import.QCURRENT_REPORT_DIR", output_root):
                result = import_q_current_file(source_file)

            self.assertEqual(result.row_count, 2)
            self.assertEqual(result.source_path, source_file.resolve())
            self.assertEqual(result.database_path.suffix, ".db")
            self.assertTrue(result.database_path.exists())
            self.assertEqual(result.database_path.parent, output_root)

            with closing(sqlite3.connect(result.database_path)) as connection:
                rows = connection.execute(
                    "SELECT time, current_ma FROM current_samples ORDER BY row_index"
                ).fetchall()
                metadata = dict(
                    connection.execute(
                        "SELECT key, value FROM import_metadata"
                    ).fetchall()
                )

            self.assertEqual(rows, [(0.0, 12.5), (1.0, 13.75)])
            self.assertEqual(metadata["source_path"], str(source_file.resolve()))
            self.assertEqual(metadata["source_extension"], ".csv")

    def test_rejects_missing_file_and_unsupported_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with self.assertRaises(FileNotFoundError):
                import_q_current_file(root / "missing.csv")

            text_file = root / "sample.txt"
            text_file.write_text("time,current_ma\n0,1\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                import_q_current_file(text_file)

    def test_rejects_file_without_required_current_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text("time,voltage\n0,12\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                import_q_current_file(source_file)


if __name__ == "__main__":
    unittest.main()