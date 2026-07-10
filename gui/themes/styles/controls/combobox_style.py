"""
ComboBox Style Factory

Responsibility:
    Generate Qt StyleSheets for all QComboBox controls.

Called By:
    - PrimaryComboBox
"""

from gui.themes.theme_manager import ThemeManager


def fn_combobox_style() -> str:

    colors = ThemeManager.fn_colors()

    return f"""
    QComboBox {{

        background: {colors.WINDOW};

        color: {colors.TEXT};

        border: 1px solid {colors.BORDER};

        border-radius: 6px;

        padding: 6px 8px;

        font-family: "Segoe UI";

        font-size: 10pt;

    }}

    QComboBox:hover {{

        border: 1px solid {colors.PRIMARY};

    }}

    QComboBox:focus {{

        border: 2px solid {colors.PRIMARY};

    }}

    QComboBox::drop-down {{

        border: none;

        width: 24px;

    }}
    """