from gui.themes.theme_manager import ThemeManager


def fn_table_style():

    colors = ThemeManager.fn_colors()

    return f"""

    QTableWidget {{

        background-color: {colors.WINDOW};

        color: {colors.TEXT};

        gridline-color: {colors.BORDER};

        border: 1px solid {colors.BORDER};

        selection-background-color: {colors.PRIMARY};

        selection-color: {colors.TEXT_INVERT};

        font-family: "Segoe UI";

        font-size: 10pt;

    }}

    QTableWidget::item{{

        padding:4px;

    }}

    QTableWidget::item:selected{{

        background:{colors.PRIMARY};

        color:{colors.TEXT_INVERT};

    }}

    

    QHeaderView::section {{

        background-color: {colors.TABLE_HEADER};

        color: {colors.TEXT};

        border: none;

        border-bottom: 1px solid {colors.BORDER};

        padding: 6px;

        font-weight: bold;

    }}

    

    """