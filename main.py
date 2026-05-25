from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from app.database import StorageDatabase
from app.gui import create_window
from app.styles.theme import apply_theme


def main() -> int:
    app = QApplication(sys.argv)
    database = StorageDatabase()
    settings = database.load_settings()
    apply_theme(app, settings.theme)
    window = create_window(database)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
