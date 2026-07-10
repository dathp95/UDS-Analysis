from gui.themes.theme_manager import ThemeManager


def fn_table_style():

    colors = ThemeManager.fn_colors()

    return f"""

    QTableWidget {{

        background: {colors.WINDOW};

        color: {colors.TEXT};

        gridline-color: {colors.BORDER};

        border: 1px solid {colors.BORDER};

        selection-background-color: {colors.PRIMARY};

        selection-color: {colors.TEXT_INVERT};

        alternate-background-color: {colors.PANEL};

        font-family: "Segoe UI";

        font-size: 10pt;

    }}

    QHeaderView::section {{

        background: {colors.TABLE_HEADER};

        color: {colors.TEXT};

        border: none;

        border-bottom: 1px solid {colors.BORDER};

        padding: 6px;

        font-weight: bold;

    }}

    """