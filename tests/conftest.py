import os
import time
from pathlib import Path

import pytest

from persistence import database


@pytest.fixture(autouse=True)
def isolated_db_path(monkeypatch, tmp_path):
    path = tmp_path / "roulette.db"
    monkeypatch.setattr(database, "DB_PATH", path)
    return path


@pytest.fixture
def initialized_db(isolated_db_path):
    database.init_db()
    return isolated_db_path


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtGui import QFontDatabase
    from PySide6.QtWidgets import QApplication

    previous = os.environ.get("QT_QPA_PLATFORM")
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication([])
    # Windows offscreen nie zawsze odczytuje systemowy katalog fontów.
    if not QFontDatabase.families() and os.name == "nt":
        font_dir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        for filename in ("segoeui.ttf", "segoeuib.ttf"):
            font = font_dir / filename
            if font.exists():
                QFontDatabase.addApplicationFont(str(font))
    yield app
    app.closeAllWindows()
    app.processEvents()
    if previous is None:
        os.environ.pop("QT_QPA_PLATFORM", None)
    else:
        os.environ["QT_QPA_PLATFORM"] = previous


@pytest.fixture
def wait_until(qapp):
    from PySide6.QtTest import QTest

    def wait(predicate, timeout=5000):
        deadline = time.monotonic() + timeout / 1000
        while not predicate():
            if time.monotonic() >= deadline:
                pytest.fail("Przekroczono czas oczekiwania na zdarzenie Qt")
            QTest.qWait(5)
        qapp.processEvents()

    return wait
