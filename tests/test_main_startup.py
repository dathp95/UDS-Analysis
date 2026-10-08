import unittest
from unittest.mock import Mock, patch

from license.manager import LicenseStatus


class MainStartupTests(unittest.TestCase):

    def test_main_starts_window_in_limited_mode_when_license_invalid(self):
        import main

        app = Mock()
        app.exec.return_value = 0
        window = Mock()
        status = LicenseStatus.invalid("missing license")

        with patch.object(main, "ensure_directories") as ensure_directories,                 patch.object(main, "ensure_start_menu_shortcut") as ensure_shortcut,                 patch.object(main, "QApplication", return_value=app) as application,                 patch.object(main.IconManager, "app", return_value=Mock()) as app_icon,                 patch.object(main.LicenseManager, "get_status", return_value=status),                 patch.object(main, "MainWindow", return_value=window) as main_window:
            result = main.main()

        self.assertEqual(result, 0)
        ensure_directories.assert_called_once_with()
        ensure_shortcut.assert_called_once_with()
        application.assert_called_once()
        app_icon.assert_called_once_with()
        main_window.assert_called_once_with(license_status=status)
        window.showMaximized.assert_called_once_with()
        self.assertIn("Limited Mode", window.setWindowTitle.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
