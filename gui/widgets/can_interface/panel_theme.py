from PySide6.QtCore import Qt
from gui.themes.theme_manager import ThemeManager


def apply_panel_theme(widget, object_name):
    """Scope container styling to this panel, never to global QWidget selectors."""
    colors = ThemeManager.fn_colors()
    widget.setObjectName(object_name)
    widget.setAttribute(Qt.WA_StyledBackground, True)
    widget.setStyleSheet(f"QWidget#{object_name} {{ background: {colors.PANEL}; border: 1px solid {colors.BORDER}; border-radius: 6px; }}")
