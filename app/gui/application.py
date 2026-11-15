"""Minimalny punkt startowy interfejsu Qt."""

import sqlite3
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from gui.main_window import MainWindow
from gui.theme import apply_theme
from persistence.database import init_db


def create_application(argv: list[str] | None = None) -> QApplication:
    app = QApplication.instance() or QApplication(sys.argv if argv is None else argv)
    app.setApplicationName("Obsidian Royale")
    if not app.property("obsidianTheme"):
        apply_theme(app)
        app.setProperty("obsidianTheme", True)
    return app


def create_main_window() -> MainWindow:
    return MainWindow()


def run(argv: list[str] | None = None) -> int:
    app = create_application(argv)
    try:
        init_db()
    except (sqlite3.Error, OSError) as exc:
        QMessageBox.critical(None, "Błąd bazy danych", f"Nie udało się przygotować bazy danych: {exc}")
        return 1
    window = create_main_window()
    window.show()
    window.start()
    return app.exec()
