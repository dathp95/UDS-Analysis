"""
LineEdit Style Factory

Responsibility:
    Generate Qt StyleSheets for all QLineEdit controls.

Called By:
    - FilterBox
    - PathSelectorWidget
    - Future dialogs
"""

from gui.themes.theme_manager import ThemeManager


def fn_lineedit_style() -> str:

    colors = ThemeManager.fn_colors()

    return f"""
    QLineEdit {{

        background-color: {colors.WINDOW};

        color: {colors.TEXT};

        border: 1px solid {colors.BORDER};

        border-radius: 6px;

        padding: 6px 8px;

        font-family: "Segoe UI";

        font-size: 10pt;

    }}

    QLineEdit:focus {{

        border: 2px solid {colors.PRIMARY};

    }}

    QLineEdit:disabled {{

        background-color: {colors.PANEL};

        color: #888888;

    }}
    """