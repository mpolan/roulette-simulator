"""Smoke Qt offscreen: import, okno, pętla zdarzeń i błąd inicjalizacji."""

import os
import sqlite3

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel

from gui import application
from persistence.player_repository import PlayerRepository


@pytest.fixture(scope="module")
def qt_app():
    previous = os.environ.get("QT_QPA_PLATFORM")
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = application.create_application([])
    yield app
    app.closeAllWindows()
    app.processEvents()
    if previous is None:
        os.environ.pop("QT_QPA_PLATFORM", None)
    else:
        os.environ["QT_QPA_PLATFORM"] = previous


def test_bootstrap_window_and_application_reuse(qt_app):
    assert isinstance(qt_app, QApplication)
    assert application.create_application([]) is qt_app
    window = application.create_bootstrap_window()
    assert window.windowTitle() == "Obsidian Royale"
    assert window.findChild(QLabel).text() == "Obsidian Royale"
    window.show()
    qt_app.processEvents()
    assert window.isVisible()
    window.close()


def test_run_initializes_isolated_database_and_enters_event_loop(qt_app, monkeypatch, isolated_db_path):
    assert not isolated_db_path.exists()
    original_create_window = application.create_bootstrap_window
    windows = []

    def create_and_close():
        window = original_create_window()
        windows.append(window)
        QTimer.singleShot(0, window.close)
        return window

    monkeypatch.setattr(application, "create_bootstrap_window", create_and_close)
    watchdog = QTimer()
    watchdog.setSingleShot(True)
    watchdog.timeout.connect(lambda: qt_app.exit(99))
    watchdog.start(5000)
    try:
        assert application.run([]) == 0
    finally:
        watchdog.stop()
    assert len(windows) == 1
    assert not windows[0].isVisible()
    assert isolated_db_path.exists()
    assert PlayerRepository().get_all_players() == []


@pytest.mark.parametrize("error", [sqlite3.OperationalError("storage"), OSError("storage")])
def test_database_failure_returns_error_without_opening_window(qt_app, monkeypatch, error):
    messages = []

    def fail_init():
        raise error

    def unexpected_window():
        pytest.fail("Okno nie powinno powstać po błędzie inicjalizacji bazy")

    monkeypatch.setattr(application, "init_db", fail_init)
    monkeypatch.setattr(application, "create_bootstrap_window", unexpected_window)
    monkeypatch.setattr(application.QMessageBox, "critical", lambda *args: messages.append(args))
    assert application.run([]) == 1
    assert len(messages) == 1
    assert messages[0][1] == "Błąd bazy danych"
    assert "Nie udało się" in messages[0][2]
