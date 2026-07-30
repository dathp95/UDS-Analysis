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

def fn_secondary_button_style():

    colors = ThemeManager.fn_colors()

    if ThemeManager.fn_is_dark():

        palette = ButtonPalette(

            background=colors.PRIMARY,

            hover=colors.PRIMARY_HOVER,

            pressed=colors.PRIMARY_PRESSED,

            text=colors.TEXT_INVERT,

            border=colors.BORDER
        )

        return _fn_base_button_style(
            palette
        )

    palette = ButtonPalette(

        background=colors.SECONDARY,

        hover=colors.SECONDARY_HOVER,

        pressed=colors.SECONDARY_PRESSED,

        text=colors.SECONDARY_TEXT,

        border=colors.BORDER
    )

    return _fn_base_button_style(
        palette
    )
