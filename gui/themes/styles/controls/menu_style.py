from PySide6.QtWidgets import QMenu

from gui.themes.theme_manager import ThemeManager


def fn_apply_menu_style(menu: QMenu) -> None:
    colors = ThemeManager.fn_colors()

    menu.setStyleSheet(
        f"""
        QMenu {{
            background-color: {colors.WINDOW};
            color: {colors.TEXT};
            border: 1px solid {colors.BORDER};
            border-radius: 6px;
            padding: 4px;
        }}

        QMenu::item {{
            background-color: transparent;
            color: {colors.TEXT};
            padding: 8px 24px 8px 12px;
            border-radius: 4px;
        }}

        QMenu::item:selected {{
            background-color: {colors.PRIMARY};
            color: {colors.WINDOW};
        }}

        QMenu::item:disabled {{
            background-color: transparent;
            color: {colors.BUTTON_DISABLED_TEXT};
        }}

        QMenu::separator {{
            height: 1px;
            background: {colors.BORDER};
            margin: 4px 8px;
        }}
        """
    )
