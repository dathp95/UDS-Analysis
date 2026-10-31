
from __future__ import annotations

import sys
import signal
from core.services.startup_service import ensure_directories

from PySide6.QtWidgets import QApplication

from gui.windows.main_window import MainWindow
from gui.windows.splash_screen import VCodeSplashScreen
from gui.themes.icon_manager import IconManager
from license.manager import LicenseManager

from utils.windows_shortcut import ensure_start_menu_shortcut


APP_NAME = "V-CODE"
APP_VERSION = "v3.0.6"
APP_AUTHOR = "AES EEIV by DAT TRAN"


def fn_window_title(license_status) -> str:
    if license_status.is_valid and license_status.license is not None:
        return (
            f"{APP_NAME} {APP_VERSION} | "
            f"{APP_AUTHOR} | "
            f"Valid until "
            f"{license_status.license.expire_date.astimezone().strftime('%d/%m/%Y %H:%M:%S')}"
        )

    return (
        f"{APP_NAME} {APP_VERSION} | "
        f"{APP_AUTHOR} | "
        "Limited Mode"
    )


def main() -> int:
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    ensure_directories()
    ensure_start_menu_shortcut()
   
    app = QApplication(sys.argv)
    app.setWindowIcon(IconManager.app())

    splash = VCodeSplashScreen()
    splash.show()
    splash.set_progress(10, "Verifying license & system environment...")

    license_status = LicenseManager.get_status()

    splash.set_progress(20, "Initializing V-CODE workspace...")

    window = MainWindow(
        license_status=license_status,
        progress_callback=splash.set_progress,
    )

    splash.set_progress(100, "Starting V-CODE...")

  

    window.setWindowTitle(
        fn_window_title(license_status)
    )

    splash.finish(window)
    window.showMaximized()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
