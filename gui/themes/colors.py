from dataclasses import dataclass

"""
Only store color values.
There are no functions.

Only data.
"""

@dataclass(frozen=True)
class ThemeColors:

    # Primary
    PRIMARY: str
    PRIMARY_HOVER: str
    PRIMARY_PRESSED: str

    # Status
    SUCCESS: str
    WARNING: str
    DANGER: str

    # Background
    WINDOW: str
    PANEL: str

    # Border
    BORDER: str

    # Text
    TEXT: str
    TEXT_INVERT: str

    # Table
    TABLE_HEADER: str

LIGHT_COLORS = ThemeColors(

    PRIMARY="#0078D4",
    PRIMARY_HOVER="#2899F5",
    PRIMARY_PRESSED="#005A9E",

    SUCCESS="#2E8B57",
    WARNING="#E67E22",
    DANGER="#C0392B",

    WINDOW="#FFFFFF",
    PANEL="#F5F5F5",

    BORDER="#D9D9D9",

    TEXT="#202020",
    TEXT_INVERT="#FFFFFF",

    TABLE_HEADER="#EFEFEF"
)

DARK_COLORS = ThemeColors(

    PRIMARY="#4CC2FF",
    PRIMARY_HOVER="#70D1FF",
    PRIMARY_PRESSED="#008ECC",

    SUCCESS="#3CB371",
    WARNING="#F4A261",
    DANGER="#FF6B6B",

    WINDOW="#1E1E1E",
    PANEL="#2B2B2B",

    BORDER="#444444",

    TEXT="#F2F2F2",
    TEXT_INVERT="#FFFFFF",

    TABLE_HEADER="#333333"
)