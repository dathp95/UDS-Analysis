import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from core.sleep_current_database import (
    get_dataset_by_name,
    get_samples,
    import_dataset,
    initialize_database,
    list_datasets,
    read_current_rows,
    replace_dataset,
)


class SleepCurrentDatabaseTests(unittest.TestCase):

    def test_initialize_database_creates_expected_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            database_file = Path(tmpdir) / "config" / "database_qcurrent" / "sleep_current.db"

            created_path = initialize_database(database_file)

            self.assertEqual(created_path, database_file.resolve())
            self.assertTrue(created_path.exists())
            with closing(sqlite3.connect(created_path)) as connection:
                dataset_columns = [
                    row[1]
                    for row in connection.execute("PRAGMA table_info(datasets)")
                ]
                sample_columns = [
                    row[1]
                    for row in connection.execute("PRAGMA table_info(current_samples)")
                ]
                indexes = [
                    row[1]
                    for row in connection.execute("PRAGMA index_list(current_samples)")
                ]

            self.assertEqual(
                dataset_columns,
                ["id", "name", "source_file", "imported_at"],
            )
            self.assertEqual(
                sample_columns,
                ["id", "dataset_id", "time", "current"],
            )
            self.assertIn("idx_current_samples_dataset_id", indexes)
            self.assertEqual(list_datasets(database_file), [])

    def test_read_csv_accepts_case_spaces_ignores_empty_rows_and_preserves_time_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text(
                " TIME , CURRENT \n00:00:00,12.5\n,\n00:00:01,13.75\n",
                encoding="utf-8",
            )

            rows = read_current_rows(source_file)

            self.assertEqual(rows, [("00:00:00", 12.5), ("00:00:01", 13.75)])

    def test_read_source_rejects_missing_unsupported_missing_columns_and_invalid_current(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with self.assertRaises(FileNotFoundError):
                read_current_rows(root / "missing.csv")

            text_file = root / "sample.txt"
            text_file.write_text("time,current\n0,1\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_current_rows(text_file)

            missing_column = root / "missing_column.csv"
            missing_column.write_text("time,voltage\n0,12\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_current_rows(missing_column)

            invalid_current = root / "invalid_current.csv"
            invalid_current.write_text("time,current\n0,nope\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_current_rows(invalid_current)

    def test_import_dataset_writes_dataset_and_samples_in_single_database(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            database_file = Path(tmpdir) / "config" / "database_qcurrent" / "sleep_current.db"
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text("time,current\n0,1.2\n1,1.3\n", encoding="utf-8")
            rows = read_current_rows(source_file)

            result = import_dataset("sample", source_file, rows, database_file)

            self.assertEqual(result.row_count, 2)
            self.assertEqual(result.dataset.name, "sample")
            self.assertEqual(get_dataset_by_name("sample", database_file), result.dataset)
            self.assertEqual(
                [(sample.time, sample.current) for sample in get_samples(result.dataset.id, database_file)],
                [("0", 1.2), ("1", 1.3)],
            )

    def test_replace_dataset_keeps_dataset_id_and_replaces_samples_atomically(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            database_file = Path(tmpdir) / "sleep_current.db"
            source_file = Path(tmpdir) / "sample.csv"
            first = import_dataset(
                "sample",
                source_file,
                [("0", 1.0), ("1", 2.0)],
                database_file,
            )

            replaced = replace_dataset(
                first.dataset.id,
                "sample",
                source_file,
                [("2", 3.0)],
                database_file,
            )

            self.assertEqual(replaced.dataset.id, first.dataset.id)
            self.assertEqual(
                [(sample.time, sample.current) for sample in get_samples(first.dataset.id, database_file)],
                [("2", 3.0)],
            )

            with self.assertRaises(ValueError):
                replace_dataset(
                    first.dataset.id,
                    "sample",
                    source_file,
                    [],
                    database_file,
                )
            self.assertEqual(
                [(sample.time, sample.current) for sample in get_samples(first.dataset.id, database_file)],
                [("2", 3.0)],
            )


if __name__ == "__main__":
    unittest.main()
