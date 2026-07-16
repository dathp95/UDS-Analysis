"""
Button Style Factory

Responsibility:
    Generate Qt StyleSheets for all button types.

Called By:
    - PrimaryButton
    - SuccessButton
    - WarningButton
    - DangerButton
"""

from gui.themes.theme_manager import ThemeManager

from gui.themes.styles.controls.button_palette import ButtonPalette



# ==========================================================
# Private
# ==========================================================

def _fn_base_button_style(
        palette: ButtonPalette

    ):

    return  f"""
        QPushButton {{

            background-color: {palette.background};

            color: {palette.text};

            border: 0px solid {palette.border};

        }}

        QPushButton:hover {{

            background-color: {palette.hover};

        }}

        QPushButton:pressed {{

            background-color: {palette.pressed};

        }}
        """

def fn_quick_access_button_style():

    colors = ThemeManager.fn_colors()

    palette = ButtonPalette(

        background=colors.QUICK_ACCESS_BACKGROUND,

        hover=colors.QUICK_ACCESS_HOVER,

        pressed=colors.QUICK_ACCESS_PRESSED,

        text=colors.TEXT_INVERT,

        border=colors.BORDER
    )

    return _fn_base_button_style(
        palette
    )