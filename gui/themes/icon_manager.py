from PySide6.QtGui import QIcon
from config.paths import ICON_DIR


class IconManager:

    @classmethod
    def app_path(cls):
        return ICON_DIR / "car-diagnostics.ico"

    @classmethod
    def app(cls):
        return QIcon(str(cls.app_path()))