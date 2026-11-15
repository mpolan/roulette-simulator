"""Minimalny punkt startowy interfejsu Qt."""

import sqlite3
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QVBoxLayout, QWidget

from persistence.database import init_db


def create_application(argv: list[str] | None = None) -> QApplication:
    return QApplication.instance() or QApplication(sys.argv if argv is None else argv)


def create_bootstrap_window() -> QWidget:
    window = QWidget()
    window.setWindowTitle("Obsidian Royale")
    window.resize(480, 240)
    layout = QVBoxLayout(window)
    label = QLabel("Obsidian Royale")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(label)
    return window


def run(argv: list[str] | None = None) -> int:
    app = create_application(argv)
    try:
        init_db()
    except (sqlite3.Error, OSError) as exc:
        QMessageBox.critical(None, "Błąd bazy danych", f"Nie udało się przygotować bazy danych: {exc}")
        return 1
    window = create_bootstrap_window()
    window.show()
    return app.exec()
