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

    /* ===========================
       Tabs
       =========================== */

    QTabWidget::pane {{

        border: 1px solid {colors.BORDER};

        background-color: {colors.WINDOW};

    }}

    QTabBar::tab {{

        background-color: {colors.PANEL};

        color: {colors.TEXT};

        border: 1px solid {colors.BORDER};

        border-bottom: none;

        padding: 8px 18px;

        margin-right: 4px;

        font-family: "Segoe UI";

        font-size: 10pt;

        font-weight: 600;

    }}

    QTabBar::tab:selected {{

        background-color: {colors.PRIMARY};

        color: {colors.TEXT_INVERT};

        border: 1px solid {colors.PRIMARY};

    }}

    QTabBar::tab:hover:!selected {{

        background-color: {colors.PRIMARY_HOVER};

        color: {colors.TEXT_INVERT};

        border: 1px solid {colors.PRIMARY_HOVER};

    }}

    QTabBar::tab:!selected {{

        margin-top: 3px;

    }}

    """
