
from __future__ import annotations

import sys
from core.services.startup_service import ensure_directories

from PySide6.QtWidgets import QApplication

from gui.windows.main_window import MainWindow
from gui.themes.icon_manager import IconManager
from license.manager import LicenseManager


APP_NAME = "V-CODE"
APP_VERSION = "v3.0.6"
APP_AUTHOR = "AES EEIV by DAT TRAN"


def fn_window_title(license_status) -> str:
    if license_status.is_valid and license_status.license is not None:
        return (
            f"{APP_NAME} {APP_VERSION} | "
            f"{APP_AUTHOR} | "
            f"Valid until "
            f"{license_status.license.expire_date.strftime('%d/%m/%Y %H:%M:%S')}"
        )

    return (
        f"{APP_NAME} {APP_VERSION} | "
        f"{APP_AUTHOR} | "
        "Limited Mode"
    )


def main() -> int:
    ensure_directories()
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "AES.EEIV.VCODE"
        )
    app = QApplication(sys.argv)
    app.setWindowIcon(IconManager.app())

    license_status = LicenseManager.get_status()

    window = MainWindow(
        license_status=license_status,
    )

    window.setWindowTitle(
        fn_window_title(license_status)
    )

    window.showMaximized()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
