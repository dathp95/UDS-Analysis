from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
    QSpacerItem,
)

from config.paths import IMAGE_DIR, RESOURCE_DIR
from gui.themes.theme_manager import ThemeManager
from gui.themes.styles.controls.scrollbar_style import fn_apply_scrollbar_style
from gui.widgets.controls.details_button import DetailsButton
from gui.widgets.controls.primary_button import PrimaryButton
from gui.widgets.controls.primary_combobox import PrimaryComboBox
from gui.widgets.controls.primary_lineedit import PrimaryLineEdit
from license.manager import LicenseManager


class LicenseSupportTab(QWidget):

    activationSucceeded = Signal(object)

    DEVICE_ID_PLACEHOLDER = "VC-XXXX-XXXX-XXXX-XXXX-XXXX"
    GUIDE_PATH = RESOURCE_DIR / "docs" / "license_support.md"
    DURATION_PRICES = {
        "1 Month": "Demo price: 150,000 VND",
        "2 Months": "Demo price: 280,000 VND",
        "3 Months": "Demo price: 390,000 VND",
        "6 Months": "Demo price: 720,000 VND",
        "12 Months": "Demo price: 1,320,000 VND",
    }

    def __init__(self):
        super().__init__()

        self._setup_ui()
        self._connect_signals()
        self.fn_refresh_theme()
        self._refresh_activation_status_from_backend()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        self.license_panel = self._build_license_panel()
        self.activation_panel = self._build_activation_panel()
        self.guide_panel = self._build_guide_panel()

        main_layout.addWidget(self.license_panel, 30)
        main_layout.addWidget(self.activation_panel, 32)
        main_layout.addWidget(self.guide_panel, 38)

    def _build_license_panel(self):
        panel = self._create_panel()
        layout = self._create_panel_layout(panel)

        self.title_label = self._create_title_label("License & Support")
        self.plan_title_label = self._create_section_label("License Plan")
        self.trial_name_label = self._create_value_label("Free Trial")
        self.trial_detail_label = self._create_body_label("First 2 months FREE")
        self.license_details_button = DetailsButton()
        self.license_details_container = self._create_details_container()
        details_layout = self.license_details_container.layout()

        self.duration_label = self._create_field_label("Duration")
        self.duration_combo = PrimaryComboBox()
        self.duration_combo.setObjectName("duration_combo")
        self.duration_combo.addItems(self.DURATION_PRICES.keys())
        self.duration_combo.setMaxVisibleItems(len(self.DURATION_PRICES))
        fn_apply_scrollbar_style(self.duration_combo.view())

        self.price_label = self._create_field_label("Price")
        self.price_value_label = self._create_value_label("")
        self._update_price_label()

        self.payment_label = self._create_section_label("Payment")
        self.qr_label = QLabel()
        self.qr_label.setObjectName("licenseSupportQr")
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setFixedSize(220, 220)
        self.qr_label.setScaledContents(False)
        self._load_support_qr()

        self.payment_helper_label = self._create_body_label(
            "Scan the QR code to complete payment."
        )
        self.contact_title_label = self._create_section_label("Contact")
        self.email_label = self._create_body_label(
            "Email: tranducdat.eng@gmail.com | tranducdatks95@gmail.com"
        )
        self.email_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.phone_label = self._create_body_label("Phone: 0329000529")
        self.phone_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(self.title_label)
        layout.addSpacing(4)
        layout.addWidget(self.plan_title_label)
        layout.addWidget(self.trial_name_label)
        layout.addWidget(self.trial_detail_label)
        layout.addWidget(self.license_details_button)
        layout.addWidget(self.license_details_container)
        details_layout.addWidget(self.duration_label)
        details_layout.addWidget(self.duration_combo)
        details_layout.addWidget(self.price_label)
        details_layout.addWidget(self.price_value_label)
        details_layout.addSpacing(8)
        details_layout.addWidget(self.payment_label)
        details_layout.addWidget(self.qr_label, 0, Qt.AlignHCenter)
        details_layout.addWidget(self.payment_helper_label)
        details_layout.addSpacing(6)
        details_layout.addWidget(self.contact_title_label)
        details_layout.addWidget(self.email_label)
        details_layout.addWidget(self.phone_label)
        layout.addStretch(1)

        return panel

    def _build_activation_panel(self):
        panel = self._create_panel()
        layout = self._create_panel_layout(panel)

        self.activation_title_label = self._create_title_label("Product Activation")
        self.activation_summary_label = self._create_body_label(
            "Payment and activation inputs are prepared for administrator support."
        )
        self.activation_details_button = DetailsButton()
        self.activation_details_container = self._create_details_container()
        details_layout = self.activation_details_container.layout()

        self.device_id_label = self._create_field_label("Device ID")
        self.device_id_edit = PrimaryLineEdit()
        self.device_id_edit.setObjectName("device_id_edit")
        self.device_id_edit.setText(self._device_id_text())
        self.device_id_edit.setReadOnly(True)

        self.copy_device_id_button = PrimaryButton("Copy ID", width=100)
        self.copy_device_id_button.setObjectName("copy_device_id_button")

        device_row = QHBoxLayout()
        device_row.setContentsMargins(0, 0, 0, 0)
        device_row.setSpacing(8)
        device_row.addWidget(self.device_id_edit, 1)
        device_row.addWidget(self.copy_device_id_button)

        self.activation_helper_label = self._create_body_label(
            "After completing payment, send your Device ID\n"
            "to the administrator."
        )

        self.activation_key_label = self._create_field_label("Activation Key")
        self.activation_key_edit = QPlainTextEdit()
        self.activation_key_edit.setObjectName("activation_key_edit")
        self.activation_key_edit.setPlaceholderText("Paste activation key here")
        self.activation_key_edit.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.activation_key_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.activation_key_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.activation_key_edit.setMinimumHeight(96)
        fn_apply_scrollbar_style(self.activation_key_edit)

        self.activate_button = PrimaryButton("Activate", width=120)
        self.activate_button.setObjectName("activate_button")

        self.status_title_label = self._create_section_label("Activation Status")
        self.status_value_label = self._create_value_label("Not Activated")
        self.status_value_label.setObjectName("activationStatusValue")
        self.status_value_label.setProperty("activated", False)
        self.edition_label = self._create_field_label("Edition:")
        self.edition_value_label = self._create_body_label("--")
        self.expire_date_label = self._create_field_label("Expire Date:")
        self.expire_date_value_label = self._create_body_label("--")
        self.remaining_label = self._create_field_label("Remaining:")
        self.remaining_value_label = self._create_body_label("--")

        layout.addWidget(self.activation_title_label)
        layout.addWidget(self.activation_summary_label)
        layout.addWidget(self.activation_details_button)
        layout.addWidget(self.activation_details_container)
        details_layout.addWidget(self.device_id_label)
        details_layout.addLayout(device_row)
        details_layout.addWidget(self.activation_helper_label)
        details_layout.addSpacing(8)
        details_layout.addWidget(self.activation_key_label)
        details_layout.addWidget(self.activation_key_edit)
        details_layout.addWidget(self.activate_button, 0, Qt.AlignLeft)
        details_layout.addSpacing(10)
        details_layout.addWidget(self.status_title_label)
        details_layout.addWidget(self.status_value_label)
        details_layout.addLayout(
            self._create_info_row(
                self.edition_label,
                self.edition_value_label,
            )
        )
        details_layout.addLayout(
            self._create_info_row(
                self.expire_date_label,
                self.expire_date_value_label,
            )
        )
        details_layout.addLayout(
            self._create_info_row(
                self.remaining_label,
                self.remaining_value_label,
            )
        )
        layout.addSpacing(4)
        layout.addStretch(1)

        return panel

    def _build_guide_panel(self):
        panel = self._create_panel()
        layout = self._create_panel_layout(panel)

        # -------------------------------------------------
        # Fixed header
        # -------------------------------------------------
        self.guide_title_label = self._create_title_label(
            "User Guide"
        )

        self.guide_summary_label = self._create_body_label(
            "Step-by-step license support notes."
        )

        self.guide_details_button = DetailsButton()

        layout.addWidget(self.guide_title_label)
        layout.addWidget(self.guide_summary_label)
        layout.addWidget(self.guide_details_button)

        # -------------------------------------------------
        # Expandable guide area
        # -------------------------------------------------
        self.guide_details_container = QWidget()
        self.guide_details_container.setVisible(False)

        self.guide_details_container.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        details_layout = QVBoxLayout(
            self.guide_details_container
        )
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(0)

        # -------------------------------------------------
        # Scrollable guide
        # -------------------------------------------------
        self.guide_browser = QTextBrowser()
        self.guide_browser.setObjectName("guide_browser")
        self.guide_browser.setReadOnly(True)
        self.guide_browser.setOpenExternalLinks(False)

        self.guide_browser.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self.guide_browser.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.guide_browser.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        fn_apply_scrollbar_style(
            self.guide_browser
        )

        self._load_guide()

        details_layout.addWidget(
            self.guide_browser,
            1,
        )

        # Guide takes remaining space when expanded
        layout.addWidget(
            self.guide_details_container,
            1,
        )

        self.guide_spacer = QSpacerItem(
            0,
            0,
            QSizePolicy.Minimum,
            QSizePolicy.Expanding,
        )

        layout.addItem(self.guide_spacer)

        # Spacer used only while Details is collapsed
        # self.guide_spacer = layout.addStretch(1)

        return panel

    def _connect_signals(self):
        self.duration_combo.currentTextChanged.connect(self._update_price_label)
        self.copy_device_id_button.clicked.connect(self.copy_device_id)
        self.activate_button.clicked.connect(self.activate_license)
        self.license_details_button.expandedChanged.connect(
            self.license_details_container.setVisible
        )
        self.activation_details_button.expandedChanged.connect(
            self.activation_details_container.setVisible
        )
        self.guide_details_button.expandedChanged.connect(
            self._toggle_guide_details
        )

    def _toggle_guide_details(self, expanded):
        self.guide_details_container.setVisible(expanded)

        if expanded:
            # Remove expanding spacer so guide can fill remaining height
            self.guide_spacer.changeSize(
                0,
                0,
                QSizePolicy.Minimum,
                QSizePolicy.Fixed,
            )
        else:
            # Spacer pushes fixed content to the top
            self.guide_spacer.changeSize(
                0,
                0,
                QSizePolicy.Minimum,
                QSizePolicy.Expanding,
            )

        self.guide_panel.layout().invalidate()
    
    @staticmethod
    def _create_panel():
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return panel

    @staticmethod
    def _create_panel_layout(panel):
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        return layout

    @staticmethod
    def _create_details_container():
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        container.setVisible(False)
        return container

    @staticmethod
    def _create_title_label(text):
        label = QLabel(text)
        label.setObjectName("licenseSupportPanelTitle")
        label.setWordWrap(True)
        return label

    @staticmethod
    def _create_section_label(text):
        label = QLabel(text)
        label.setObjectName("licenseSupportSectionTitle")
        label.setWordWrap(True)
        return label

    @staticmethod
    def _create_field_label(text):
        label = QLabel(text)
        label.setObjectName("licenseSupportFieldLabel")
        label.setWordWrap(True)
        return label

    @staticmethod
    def _create_value_label(text):
        label = QLabel(text)
        label.setObjectName("licenseSupportValueLabel")
        label.setWordWrap(True)
        return label

    @staticmethod
    def _create_body_label(text):
        label = QLabel(text)
        label.setObjectName("licenseSupportBodyLabel")
        label.setWordWrap(True)
        return label

    @staticmethod
    def _create_info_row(label, value_label):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(label)
        row.addWidget(value_label, 1)
        return row

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

    def _load_guide(self):
        try:
            guide_text = self.GUIDE_PATH.read_text(encoding="utf-8")
        except OSError:
            guide_text = (
                "# License Support\n\n"
                "The activation workflow is being prepared."
            )

        self.guide_browser.setMarkdown(guide_text)

    @staticmethod
    def _support_qr_path():
        preferred_path = IMAGE_DIR / "support.qr.jpg"
        if preferred_path.exists():
            return preferred_path

        return IMAGE_DIR / "support_qr.jpg"

    def _update_price_label(self):
        duration = self.duration_combo.currentText()
        self.price_value_label.setText(
            self.DURATION_PRICES.get(duration, "Demo price: --")
        )

    def copy_device_id(self):
        QApplication.clipboard().setText(self.device_id_edit.text())

    def activate_license(self):
        activation_key = self.activation_key_edit.toPlainText().strip()
        result = LicenseManager.activate(activation_key)
        if not result.success or result.license is None:
            self._show_inactive_license("Activation Failed", result.error_message)
            return

        self._show_activated_license(result.license)
        self.activationSucceeded.emit(result.license)

    def _refresh_activation_status_from_backend(self):
        status = LicenseManager.get_status()
        if status.is_valid and status.license is not None:
            self._show_activated_license(status.license)
            return

        self._show_inactive_license("Not Activated", status.error_message)

    def _show_activated_license(self, license_model):
        self.status_value_label.setText(" ● Activated ")
        self.status_value_label.setProperty("activated", True)
        self.status_value_label.style().unpolish(self.status_value_label)
        self.status_value_label.style().polish(self.status_value_label)
        self.status_value_label.setToolTip("")
        self.edition_value_label.setText(license_model.edition)
        self.expire_date_value_label.setText(
            license_model.expire_date.strftime("%d/%m/%Y %H:%M:%S")
        )
        self.remaining_value_label.setText(
            f"{max(license_model.days_remaining, 0)} day(s)"
        )

    def _show_inactive_license(self, status_text, tooltip=""):
        self.status_value_label.setText(status_text)
        self.status_value_label.setProperty("activated", False)
        self.status_value_label.style().unpolish(self.status_value_label)
        self.status_value_label.style().polish(self.status_value_label)
        self.status_value_label.setToolTip(tooltip)
        self.edition_value_label.setText("--")
        self.expire_date_value_label.setText("--")
        self.remaining_value_label.setText("--")

    @staticmethod
    def _device_id_text():
        try:
            return LicenseManager.get_device_id()
        except Exception:
            return LicenseSupportTab.DEVICE_ID_PLACEHOLDER

    def fn_refresh_theme(self):
        colors = ThemeManager.fn_colors()
        self.setStyleSheet(
            f"""
            QFrame {{
                background: {colors.PANEL};
                border: 1px solid {colors.BORDER};
                border-radius: 6px;
            }}
            QLabel {{
                color: {colors.TEXT};
                border: none;
                background: transparent;
                font-size: 13px;
            }}
            QLabel#licenseSupportPanelTitle {{
                font-size: 18px;
                font-weight: 700;
            }}
            QLabel#licenseSupportSectionTitle {{
                font-size: 16px;
                font-weight: 700;
                margin-top: 8px;
            }}
            QLabel#licenseSupportFieldLabel {{
                color: {colors.TEXT};
                font-weight: 600;
            }}
            QLabel#licenseSupportValueLabel {{
                font-size: 14px;
                font-weight: 700;
            }}
            QLabel#activationStatusValue[activated="true"] {{
                color: {colors.SUCCESS};
                font-size: 14px;
                font-weight: 700;
            }}
            QLabel#licenseSupportQr {{
                background: {colors.WINDOW};
                border: 1px solid {colors.BORDER};
                border-radius: 6px;
            }}
            QTextBrowser, QPlainTextEdit {{
                background: {colors.WINDOW};
                color: {colors.TEXT};
                border: 1px solid {colors.BORDER};
                border-radius: 6px;
                padding: 8px;
                font-size: 10pt;
            }}
            """
        )
        self.duration_combo.fn_refresh_theme()
        self.device_id_edit.fn_refresh_theme()
        self.copy_device_id_button.fn_refresh_theme()
        self.activate_button.fn_refresh_theme()
        self.license_details_button.fn_refresh_theme()
        self.activation_details_button.fn_refresh_theme()
        self.guide_details_button.fn_refresh_theme()
        fn_apply_scrollbar_style(self.duration_combo.view())
        fn_apply_scrollbar_style(self.activation_key_edit)
        fn_apply_scrollbar_style(self.guide_browser)
