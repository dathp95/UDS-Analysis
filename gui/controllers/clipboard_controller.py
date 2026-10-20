from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
)

from core.transaction_formatter import fn_format_transaction_rows_tsv


class ClipboardController:

    # ==========================================
    # Public
    # ==========================================

    def fn_copy(
        self,
        parent,
        rows: list[dict],
    ):

        try:

            if not rows:
                QMessageBox.information(parent, "Copy", "No visible transactions to copy.")
                return

            content = fn_format_transaction_rows_tsv(rows)

            QApplication.clipboard().setText(
                content
            )

            QMessageBox.information(
                parent,
                "Copy",
                f"Copied {len(rows)} transaction{'s' if len(rows) != 1 else ''}.",
            )

        except Exception as error:

            QMessageBox.warning(
                parent,
                "Copy",
                str(error),
            )
