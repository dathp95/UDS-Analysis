
from __future__ import annotations

import sys
from core.services.startup_service import ensure_directories

from PySide6.QtWidgets import QApplication, QMessageBox

from gui.windows.main_window import MainWindow
from license.exceptions import LicenseError
from license.manager import LicenseManager


APP_NAME = "V-CODE"
APP_VERSION = "v1.0.2"
APP_AUTHOR = "AES EEIV by DAT TRAN"


def main() -> int:
    ensure_directories()
    app = QApplication(sys.argv)

    try:
        license = LicenseManager.validate()

    except LicenseError as exc:
        QMessageBox.critical(
            None,
            "License Error",
            str(exc),
        )
        return 1

    window = MainWindow()

    window.setWindowTitle(
        f"{APP_NAME} {APP_VERSION} | "
        f"{APP_AUTHOR} | "
        f"Valid until "
        f"{license.expire_date.strftime('%d/%m/%Y %H:%M:%S')}"
    )

    window.showMaximized()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
