import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from core.sleep_current_database import (
    database_path_for_source,
    get_dataset_by_name,
    get_samples,
    import_dataset,
    initialize_database,
    list_datasets,
    normalize_current_data,
    read_current_rows,
    replace_dataset,
)


class SleepCurrentDatabaseTests(unittest.TestCase):

    def test_initialize_database_creates_expected_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            database_file = Path(tmpdir) / "config" / "database_qcurrent" / "sample.db"

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
                ["id", "name", "source_file", "imported_at", "detected_channel"],
            )
            self.assertEqual(
                sample_columns,
                ["id", "dataset_id", "time", "current_A", "current_mA"],
            )
            self.assertIn("idx_current_samples_dataset_id", indexes)
            self.assertEqual(list_datasets(database_file.parent), [])

    def test_list_datasets_ignores_non_q_current_database_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            database_dir = Path(tmpdir) / "database_qcurrent"
            database_dir.mkdir(parents=True)
            with closing(sqlite3.connect(database_dir / "other.db")) as connection:
                connection.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
                connection.commit()

            self.assertEqual(list_datasets(database_dir), [])
    def test_database_path_for_source_uses_database_directory_and_source_stem(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            database_dir = Path(tmpdir) / "config" / "database_qcurrent"
            source_file = Path(tmpdir) / "Q_5Z.4.7.0 V3_1.CSV"

            database_file = database_path_for_source(source_file, database_dir)

            self.assertEqual(database_file, database_dir.resolve() / "Q_5Z.4.7.0 V3_1.db")
            self.assertTrue(database_dir.exists())
    def test_initialize_database_migrates_old_current_sample_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            database_file = Path(tmpdir) / "sample.db"
            with closing(sqlite3.connect(database_file)) as connection:
                connection.execute(
                    """
                    CREATE TABLE datasets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        source_file TEXT,
                        imported_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE current_samples (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dataset_id INTEGER NOT NULL,
                        time TEXT NOT NULL,
                        current REAL NOT NULL
                    )
                    """
                )
                connection.execute(
                    "INSERT INTO datasets (name, source_file, imported_at) VALUES (?, ?, ?)",
                    ("legacy", "legacy.csv", "2026-09-23T00:00:00"),
                )
                connection.execute(
                    "INSERT INTO current_samples (dataset_id, time, current) VALUES (?, ?, ?)",
                    (1, "00:00:00.000", -0.0169),
                )
                connection.commit()

            initialize_database(database_file)

            samples = get_samples(1, database_file)
            self.assertEqual(len(samples), 1)
            self.assertEqual(samples[0].current_A, -0.0169)
            self.assertEqual(samples[0].current_mA, -16.9)
            self.assertIsNone(get_dataset_by_name("legacy", database_file).detected_channel)

    def test_normalize_detects_trigger_time_and_single_average_channel(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text(
                " Trigger time , No1 Average Ch7 \n"
                ",A\n"
                "26-09-11 11:41:29.036,-1.69E-02\n"
                "26-09-11 11:41:30.079,-1.73E-02\n",
                encoding="utf-8",
            )

            normalized = normalize_current_data(source_file)

            self.assertEqual(normalized.detected_channel, "No1 Average Ch7")
            self.assertEqual(
                normalized.rows,
                [
                    ("26-09-11 11:41:29.036", -0.0169, -16.9),
                    ("26-09-11 11:41:30.079", -0.0173, -17.3),
                ],
            )
            self.assertEqual(read_current_rows(source_file), normalized.rows)

    def test_normalize_rejects_missing_unsupported_missing_columns_invalid_and_multiple_channels(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with self.assertRaises(FileNotFoundError):
                normalize_current_data(root / "missing.csv")

            text_file = root / "sample.txt"
            text_file.write_text("Trigger time,No1 Average Ch1\n0,1\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                normalize_current_data(text_file)

            missing_column = root / "missing_column.csv"
            missing_column.write_text("Trigger time,voltage\n0,12\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "current column"):
                normalize_current_data(missing_column)

            invalid_only = root / "invalid_only.csv"
            invalid_only.write_text(
                "Trigger time,No1 Average Ch1\n,A\n0,nope\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "valid measurement"):
                normalize_current_data(invalid_only)

            multiple = root / "multiple.csv"
            multiple.write_text(
                "Trigger time,No1 Average Ch1,No1 Average Ch2\n0,1,2\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "No1 Average Ch1.*No1 Average Ch2"):
                normalize_current_data(multiple)

    def test_import_dataset_writes_dataset_and_ampere_milliamp_samples(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            database_file = Path(tmpdir) / "config" / "database_qcurrent" / "sample.db"
            source_file = Path(tmpdir) / "sample.csv"
            source_file.write_text(
                "Trigger time,No1 Average Ch10\n0,-1.2E-03\n1,-1.3E-03\n",
                encoding="utf-8",
            )
            normalized = normalize_current_data(source_file)

            result = import_dataset(
                "sample",
                source_file,
                normalized.rows,
                database_file,
                detected_channel=normalized.detected_channel,
            )

            self.assertEqual(result.row_count, 2)
            self.assertEqual(result.dataset.name, "sample")
            self.assertEqual(result.dataset.detected_channel, "No1 Average Ch10")
            self.assertEqual(get_dataset_by_name("sample", database_file), result.dataset)
            self.assertEqual(result.dataset.database_path, database_file.resolve())
            self.assertEqual(list_datasets(database_file.parent), [result.dataset])
            self.assertEqual(
                [
                    (sample.time, sample.current_A, sample.current_mA)
                    for sample in get_samples(result.dataset.id, database_file)
                ],
                [("0", -0.0012, -1.2), ("1", -0.0013, -1.3)],
            )

    def test_replace_dataset_keeps_dataset_id_and_replaces_samples_atomically(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            database_file = Path(tmpdir) / "sample.db"
            source_file = Path(tmpdir) / "sample.csv"
            first = import_dataset(
                "sample",
                source_file,
                [("0", 0.001, 1.0), ("1", 0.002, 2.0)],
                database_file,
                detected_channel="No1 Average Ch1",
            )

            replaced = replace_dataset(
                first.dataset.id,
                "sample",
                source_file,
                [("2", 0.003, 3.0)],
                database_file,
                detected_channel="No1 Average Ch2",
            )

            self.assertEqual(replaced.dataset.id, first.dataset.id)
            self.assertEqual(replaced.dataset.detected_channel, "No1 Average Ch2")
            self.assertEqual(
                [
                    (sample.time, sample.current_A, sample.current_mA)
                    for sample in get_samples(first.dataset.id, database_file)
                ],
                [("2", 0.003, 3.0)],
            )

            with self.assertRaises(ValueError):
                replace_dataset(
                    first.dataset.id,
                    "sample",
                    source_file,
                    [],
                    database_file,
                    detected_channel="No1 Average Ch2",
                )
            self.assertEqual(
                [
                    (sample.time, sample.current_A, sample.current_mA)
                    for sample in get_samples(first.dataset.id, database_file)
                ],
                [("2", 0.003, 3.0)],
            )


if __name__ == "__main__":
    unittest.main()
