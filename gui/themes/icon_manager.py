from pathlib import Path
from PySide6.QtGui import QIcon


class IconManager:

    ICON_DIR = Path("gui/resources/icons")

    @classmethod
    def app(cls):

        return QIcon(
            str(cls.ICON_DIR / "webhook.svg")
        )