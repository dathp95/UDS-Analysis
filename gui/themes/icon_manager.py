from PySide6.QtGui import QIcon
from config.paths import ICON_DIR


class IconManager:

    @classmethod
    def app(cls):
        return QIcon(str(ICON_DIR / "car-diagnostics.ico"))