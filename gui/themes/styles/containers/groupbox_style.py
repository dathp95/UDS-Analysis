"""
GroupBox Style Factory

Responsibility:
    Generate Qt StyleSheets for all QGroupBox controls.

Called By:
    - PrimaryGroupBox
"""

from gui.themes.theme_manager import ThemeManager


def fn_groupbox_style() -> str:

    colors = ThemeManager.fn_colors()

    return f"""
    QGroupBox {{

        background: {colors.PANEL};

        color: {colors.TEXT};

        border: 1px solid {colors.BORDER};

        border-radius: 8px;

        margin-top: 12px;

        padding: 12px;

        font-family: "Segoe UI";

        font-size: 10pt;

        font-weight: bold;

    }}

    QGroupBox::title {{

        subcontrol-origin: margin;

        left: 12px;

        padding: 0px 6px;

        color: {colors.TEXT};

    }}
    """