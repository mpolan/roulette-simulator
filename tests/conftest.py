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
