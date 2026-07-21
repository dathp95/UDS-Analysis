from gui.themes.theme_manager import ThemeManager

from PySide6.QtWidgets import QAbstractScrollArea


def fn_apply_scrollbar_style(widget: QAbstractScrollArea):

    style = fn_scrollbar_style()

    widget.verticalScrollBar().setStyleSheet(style)
    widget.horizontalScrollBar().setStyleSheet(style)





def fn_scrollbar_style():

    colors = ThemeManager.fn_colors()

    return f"""
    QScrollBar:vertical {{
        background: transparent;
        border: none;
        width: 6px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: {colors.SCROLLBAR};
        border-radius: 3px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {colors.SCROLLBAR_HOVER};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical,
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        background: transparent;
        border: none;
        width: 0px;
        height: 0px;
    }}

    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: transparent;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        border: none;
        height: 6px;
        margin: 0px;
    }}

    QScrollBar::handle:horizontal {{
        background: {colors.SCROLLBAR};
        border-radius: 3px;
        min-width: 30px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {colors.SCROLLBAR_HOVER};
    }}

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {{
        background: transparent;
    }}
    """