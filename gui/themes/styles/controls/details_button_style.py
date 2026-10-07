from gui.themes.theme_manager import ThemeManager


def fn_details_button_style():
    colors = ThemeManager.fn_colors()

    return f"""
        QPushButton {{
            background-color: transparent;
            color: {colors.TEXT};
            border: 0px solid transparent;
            border-radius: 4px;
            padding: 4px 6px;
            text-align: left;
            font-family: "Segoe UI";
            font-size: 10pt;
            font-weight: 600;
        }}

        QPushButton:hover {{
            background-color: {colors.SECONDARY_HOVER};
            color: {colors.TEXT};
        }}

        QPushButton:pressed {{
            background-color: {colors.SECONDARY_PRESSED};
            color: {colors.TEXT};
        }}
    """
