from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
)

from core.services.clipboard_service import ClipboardService


class ClipboardController:

    def __init__(self):

        self.clipboard_service = ClipboardService()

    # ==========================================
    # Public
    # ==========================================

    def fn_copy(
        self,
        parent,
        log_file: str,
    ):

        try:

            asc_file, content = (
                self.clipboard_service.fn_read_asc_content(
                    log_file
                )
            )

            QApplication.clipboard().setText(
                content
            )

            QMessageBox.information(
                parent,
                "Copy",
                f"Copied ASC log:\n\n{asc_file}",
            )

        except Exception as error:

            QMessageBox.warning(
                parent,
                "Copy",
                str(error),
            )