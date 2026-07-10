from gui.themes.theme import ThemeType
from gui.themes.colors import (
    LIGHT_COLORS,
    DARK_COLORS,
    ThemeColors
)

"""
Manage the current theme.
"""
class ThemeManager:

    _theme = ThemeType.LIGHT

    _colors = LIGHT_COLORS

    @classmethod
    def fn_theme(cls) -> ThemeType:

        return cls._theme
    
    @classmethod
    def fn_colors(cls) -> ThemeColors:

        return cls._colors
    
    @classmethod
    def fn_set_theme(
        cls,
        theme: ThemeType
    ):

        cls._theme = theme

        if theme == ThemeType.DARK:

            cls._colors = DARK_COLORS

        else:

            cls._colors = LIGHT_COLORS

    @classmethod
    def fn_is_dark(cls):

        return cls._theme == ThemeType.DARK
    
    @classmethod
    def fn_is_light(cls):

        return cls._theme == ThemeType.LIGHT