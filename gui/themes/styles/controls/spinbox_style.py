"""
SpinBox Style Factory

Responsibility:
    Generate Qt StyleSheets for all QSpinBox controls.
"""

from gui.themes.theme_manager import ThemeManager


def fn_spinbox_style() -> str:

    colors = ThemeManager.fn_colors()

    return f"""
    QSpinBox {{

        background-color: {colors.WINDOW};

        color: {colors.TEXT};

        border: 1px solid {colors.BORDER};

        border-radius: 6px;

        padding: 6px 26px 6px 8px;

        font-family: "Segoe UI";

        font-size: 10pt;

    }}

    QSpinBox:hover {{

        border: 1px solid {colors.PRIMARY};

    }}

    QSpinBox:focus {{

        border: 2px solid {colors.PRIMARY};

    }}

    QSpinBox:disabled {{

        background-color: {colors.PANEL};

        color: {colors.BUTTON_DISABLED_TEXT};

        border: 1px solid {colors.BUTTON_DISABLED_BORDER};

    }}

    QSpinBox::up-button,
    QSpinBox::down-button {{

        background-color: {colors.PRIMARY};

        border-left: 1px solid {colors.PRIMARY_PRESSED};

        width: 22px;

    }}

    QSpinBox::up-button {{

        subcontrol-origin: border;

        subcontrol-position: top right;

        border-top-right-radius: 5px;

    }}

    QSpinBox::down-button {{

        subcontrol-origin: border;

        subcontrol-position: bottom right;

        border-bottom-right-radius: 5px;

    }}

    QSpinBox::up-button:hover,
    QSpinBox::down-button:hover {{

        background-color: {colors.PRIMARY_HOVER};

    }}

    QSpinBox::up-button:pressed,
    QSpinBox::down-button:pressed {{

        background-color: {colors.PRIMARY_PRESSED};

    }}

    QSpinBox::up-button:disabled,
    QSpinBox::down-button:disabled {{

        background-color: {colors.BUTTON_DISABLED};

        border-left: 1px solid {colors.BUTTON_DISABLED_BORDER};

    }}

    QSpinBox::up-arrow,
    QSpinBox::down-arrow {{

        width: 0px;

        height: 0px;

        image: none;

    }}

    QSpinBox::up-arrow {{

        border-left: 5px solid transparent;

        border-right: 5px solid transparent;

        border-bottom: 7px solid {colors.TEXT_INVERT};

    }}

    QSpinBox::down-arrow {{

        border-left: 5px solid transparent;

        border-right: 5px solid transparent;

        border-top: 7px solid {colors.TEXT_INVERT};

    }}

    QSpinBox::up-arrow:disabled {{

        border-bottom: 7px solid {colors.BUTTON_DISABLED_TEXT};

    }}

    QSpinBox::down-arrow:disabled {{

        border-top: 7px solid {colors.BUTTON_DISABLED_TEXT};

    }}
    """