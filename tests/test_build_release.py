import json
import tempfile
import unittest
from pathlib import Path

from build_release import prepare_release, validate_no_archives


class BuildReleaseTests(unittest.TestCase):

    def create_project(self, root: Path) -> None:
        for folder in ("config", "license", "shortcuts"):
            path = root / folder
            path.mkdir(parents=True)
            (path / "placeholder.txt").write_text(folder, encoding="utf-8")
        (root / "README.txt").write_text("V-CODE release", encoding="utf-8")

    def test_prepare_release_normalizes_nuitka_runtime_and_validates_archives(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project = root / "project"
            runtime = root / "build" / "nuitka" / "main.dist"
            dist = root / "dist" / "EEIV Diagnostic"
            project.mkdir()
            runtime.mkdir(parents=True)
            self.create_project(project)
            (runtime / "V-CODE.exe").write_text("exe", encoding="utf-8")
            internal = runtime / "_internal"
            internal.mkdir()
            (internal / "runtime.pyd").write_text("pyd", encoding="utf-8")

            prepare_release(
                project=project,
                dist=dist,
                runtime_source=runtime,
                validate_archives=True,
            )

            self.assertTrue((dist / "V-CODE.exe").exists())
            self.assertTrue((dist / "_internal" / "runtime.pyd").exists())
            self.assertTrue((dist / "config" / "placeholder.txt").exists())
            self.assertTrue((dist / "license" / "placeholder.txt").exists())
            self.assertTrue((dist / "shortcuts" / "placeholder.txt").exists())
            self.assertTrue((dist / "README.txt").exists())
            self.assertTrue((dist / "output" / "Report_LogAnalyzer").is_dir())
            self.assertTrue((dist / "output" / "Report_CodingValue").is_dir())
            self.assertTrue((dist / "output" / "Report_QCurrent").is_dir())
            release_features = json.loads(
                (dist / "config" / "release_features.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                release_features,
                {"deactivated_features": ["can_interface"]},
            )

    def test_validate_no_archives_fails_instead_of_deleting_forbidden_archive(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dist = Path(tmpdir) / "EEIV Diagnostic"
            archive = dist / "_internal" / "base_library.zip"
            archive.parent.mkdir(parents=True)
            archive.write_text("zip", encoding="utf-8")

            with self.assertRaises(SystemExit):
                validate_no_archives(dist)

            self.assertTrue(archive.exists())

    def test_prepare_release_can_skip_archive_validation_for_legacy_pyinstaller(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            project = root / "project"
            dist = root / "dist" / "EEIV Diagnostic"
            project.mkdir()
            self.create_project(project)
            archive = dist / "_internal" / "base_library.zip"
            archive.parent.mkdir(parents=True)
            archive.write_text("zip", encoding="utf-8")

            prepare_release(
                project=project,
                dist=dist,
                validate_archives=False,
            )

            self.assertTrue(archive.exists())

    def test_release_batch_uses_nuitka_standalone_and_security_validation(self):
        script = Path("release.bat").read_text(encoding="utf-8").lower()

        self.assertIn("python -m nuitka", script)
        self.assertIn("--standalone", script)
        self.assertIn("--enable-plugin=pyside6", script)
        self.assertIn("--windows-console-mode=disable", script)
        self.assertIn(
            "--windows-icon-from-ico=gui\\resources\\images\\car-diagnostics.ico",
            script,
        )
        self.assertIn("--include-data-dir=gui\\resources=gui\\resources", script)
        self.assertIn("--validate-archives", script)
        self.assertNotIn("--onefile", script)
        self.assertIn("build_release.py", script)

    def test_pyinstaller_rollback_script_is_preserved(self):
        script = Path("release_pyinstaller.bat").read_text(encoding="utf-8").lower()

        self.assertIn("pyinstaller uds-analysis.spec --clean", script)
        self.assertIn("python build_release.py", script)


if __name__ == "__main__":
    unittest.main()
