"""
CheckBox Style Factory

Responsibility:
    Generate Qt StyleSheets for all QCheckBox controls.

Called By:
    - PrimaryCheckBox
"""

from gui.themes.theme_manager import ThemeManager


def fn_checkbox_style() -> str:

    colors = ThemeManager.fn_colors()

    return f"""
    QCheckBox {{

        color: {colors.TEXT};

        spacing: 8px;

        font-family: "Segoe UI";

        font-size: 10pt;

    }}

    QCheckBox::indicator {{

        width: 16px;

        height: 16px;

        border: 1px solid {colors.BORDER};

        border-radius: 3px;

        background: {colors.WINDOW};

    }}

    QCheckBox::indicator:checked {{

        background: {colors.PRIMARY};

        border: 1px solid {colors.PRIMARY};

    }}

    QCheckBox::indicator:hover {{

        border: 1px solid {colors.PRIMARY};

    }}
    """