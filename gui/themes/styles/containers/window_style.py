"""
Window Style Factory

Responsibility:
    Generate global Qt StyleSheets for
    QMainWindow and QWidget.

Called By:
    - MainWindow
"""

from gui.themes.theme_manager import ThemeManager


def fn_window_style() -> str:

    colors = ThemeManager.fn_colors()

    return f"""

    /* ===========================
       Main Window
       =========================== */

    QMainWindow {{

        background-color: {colors.WINDOW};

        color: {colors.TEXT};

    }}

    /* ===========================
       Default Widget
       =========================== */

    QWidget {{

        background-color: {colors.WINDOW};

        color: {colors.TEXT};

        font-family: "Segoe UI";

        font-size: 10pt;

    }}

    """