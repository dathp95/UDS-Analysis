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

    colors = ThemeManager.fn_colors()

    return  f"""
        QPushButton {{

            background-color: {palette.background};

            color: {palette.text};

            border: 1px solid {palette.border};


            font-family: "Segoe UI";

            font-size: 10pt;

            font-weight: 600;

            text-align: left;

            padding-left: 16px;
            padding-right: 10px;

            min-height: 34px;
            border-radius: 4px;

        }}

        QPushButton:disabled {{

            background-color: {colors.BUTTON_DISABLED};

            color: {colors.BUTTON_DISABLED_TEXT};

            border: 1px solid {colors.BUTTON_DISABLED_BORDER};

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