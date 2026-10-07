from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

from config.paths import IMAGE_DIR


class LicenseSupportTab(QWidget):

    def __init__(self):
        super().__init__()

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )
        main_layout.setSpacing(14)

        self.title_label = QLabel("Support the development 💝💝💝")
        self.title_label.setObjectName("licenseSupportTitle")
        self.title_label.setAlignment(Qt.AlignLeft)

        self.description_label = QLabel(
            "Enjoying the tool? Buy me a coffee!"
        )
        self.description_label.setWordWrap(True)

        self.qr_label = QLabel()
        self.qr_label.setObjectName("licenseSupportQr")
        self.qr_label.setAlignment(Qt.AlignLeft)
        self.qr_label.setFixedSize(260, 260)
        self.qr_label.setScaledContents(False)
        self._load_support_qr()

        self.contact_title_label = QLabel("Contact")
        self.contact_title_label.setObjectName("licenseSupportContactTitle")

        self.email_label = QLabel(
            "Email: tranducdat.eng@gmail.com | tranducdatks95@gmail.com"
        )
        self.email_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.phone_label = QLabel("Phone: 0329000529")
        self.phone_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.description_label)
        main_layout.addWidget(self.qr_label)
        main_layout.addSpacing(6)
        main_layout.addWidget(self.contact_title_label)
        main_layout.addWidget(self.email_label)
        main_layout.addWidget(self.phone_label)
        main_layout.addStretch(1)

    def _load_support_qr(self):
        image_path = self._support_qr_path()
        self.support_qr_pixmap = QPixmap(str(image_path))
        display_pixmap = self.support_qr_pixmap.scaled(
            self.qr_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.qr_label.setPixmap(display_pixmap)
        self.qr_label.setToolTip(str(image_path))

    @staticmethod
    def _support_qr_path():
        preferred_path = IMAGE_DIR / "support.qr.jpg"
        if preferred_path.exists():
            return preferred_path

        return IMAGE_DIR / "support_qr.jpg"

    def fn_refresh_theme(self):
        self.setStyleSheet(
            """
            QLabel#licenseSupportTitle {
                font-size: 22px;
                font-weight: 700;
            }
            QLabel#licenseSupportContactTitle {
                font-size: 16px;
                font-weight: 700;
                margin-top: 8px;
            }
            QLabel {
                font-size: 13px;
            }
            """
        )
