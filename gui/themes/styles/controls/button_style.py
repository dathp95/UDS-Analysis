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
from gui.themes.theme_manager import ThemeManager

# ==========================================================
# Private
# ==========================================================

def _fn_base_button_style(
        palette: ButtonPalette

    ):
    colors = ThemeManager.fn_colors()

    return  f"""
        QPushButton {{

            background-color: {palette.background};

            color: {palette.text};

            border: 0px solid {palette.border};

            font-family: "Segoe UI";

            font-size: 10pt;

            font-weight: 600;


        }}

        QPushButton:hover {{

            background-color: {palette.hover};

        }}

        QPushButton:disabled {{

            background-color: {colors.BUTTON_DISABLED};

            color: {colors.BUTTON_DISABLED_TEXT};

            border: 1px solid {colors.BUTTON_DISABLED_BORDER};

        }}

        QPushButton:pressed {{

            background-color: {palette.pressed};

        }}
        """

def fn_primary_button_style():

    colors = ThemeManager.fn_colors()

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


def fn_cancel_button_style():

    colors = ThemeManager.fn_colors()

    palette = ButtonPalette(
        background=colors.SECONDARY,
        hover=colors.SECONDARY_HOVER,
        pressed=colors.SECONDARY_PRESSED,
        text=colors.TEXT if ThemeManager.fn_is_dark() else colors.SECONDARY_TEXT,
        border=colors.BORDER,
    )

    return _fn_base_button_style(
        palette
    )

def fn_quick_access_button_style():

    colors = ThemeManager.fn_colors()

    palette = ButtonPalette(

        background=colors.QUICK_ACCESS_BACKGROUND,

        hover=colors.QUICK_ACCESS_HOVER,

        pressed=colors.QUICK_ACCESS_PRESSED,

        text=colors.QUICK_ACCESS_TEXT,

        border=colors.BORDER
    )

    return _fn_base_button_style(
        palette
    )
