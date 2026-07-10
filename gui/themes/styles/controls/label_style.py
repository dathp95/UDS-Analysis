"""
Label Style Factory

Responsibility:
    Generate Qt StyleSheets for all QLabel controls.

Called By:
    - PrimaryLabel
"""

from gui.themes.theme_manager import ThemeManager


def fn_label_style() -> str:

    colors = ThemeManager.fn_colors()

    return f"""
    QLabel {{

        color: {colors.TEXT};

        background: transparent;

        font-family: "Segoe UI";

        font-size: 10pt;

    }}
    """