"""Transakcje i ponawianie zapisu na izolowanej bazie SQLite."""

import importlib.util
import sqlite3
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from domain.bet import Bet, BetType
from domain.game import Game
from domain.player import Player
from persistence import database
from persistence.player_repository import PlayerRepository
from persistence.round_repository import RoundRepository
from services.game_session import GameSession
from services.session_factory import create_game_session


def test_profiles_default_balance_uniqueness_and_session_factory(initialized_db):
    players = PlayerRepository()
    profile = players.add_player("Alicja")
    assert profile.balance == 1000
    with pytest.raises(sqlite3.IntegrityError):
        players.add_player("Alicja")
    assert players.get_all_players() == [profile]
    session = create_game_session(profile.id)
    assert session.player_id == profile.id
    assert session.game.player.name == "Alicja"
    assert session.game.player.balance == 1000
    assert players.get_player(-1) is None
    with pytest.raises(LookupError):
        create_game_session(-1)
    with pytest.raises(ValueError):
        players.update_balance(profile.id, -1)
    with pytest.raises(LookupError):
        players.update_balance(-1, 50)


def test_round_retry_reuses_result_balance_and_single_spin(initialized_db, monkeypatch):
    profile = PlayerRepository().add_player("Retry")
    game = Game(Player(profile.name, profile.balance))
    pocket = next(p for p in game.wheel.pockets if p.number == 1)
    spin = Mock(return_value=pocket)
    monkeypatch.setattr(game.wheel, "spin", spin)
    repository = RoundRepository()
    real_save = repository.save_round
    save = Mock(side_effect=[sqlite3.OperationalError("disk"), sqlite3.OperationalError("disk"), None])
    attempts = []

    def flaky_save(**kwargs):
        attempts.append(kwargs)
        save()
        return real_save(**kwargs)

    monkeypatch.setattr(repository, "save_round", flaky_save)
    session = GameSession(profile.id, game, repository)
    game.place_bet(Bet(10, BetType.RED))
    with pytest.raises(sqlite3.OperationalError):
        session.spin_and_save()
    assert session.has_pending_round
    assert game.player.balance == 1010
    assert game.current_bets == ()
    with pytest.raises(RuntimeError):
        session.spin_and_save()
    with pytest.raises(sqlite3.OperationalError):
        session.save_pending_round()
    assert session.has_pending_round
    assert PlayerRepository().get_player(profile.id).balance == 1000
    assert repository.get_player_rounds(profile.id) == []
    result = session.save_pending_round()
    assert not session.has_pending_round
    assert all(attempt["result"] is result for attempt in attempts)
    assert [attempt["balance_after"] for attempt in attempts] == [1010, 1010, 1010]
    assert spin.call_count == 1
    assert game.player.balance == 1010
    assert PlayerRepository().get_player(profile.id).balance == 1010
    assert len(repository.get_player_rounds(profile.id)) == 1
    stored_bets = repository.get_player_bets(profile.id)
    assert len(stored_bets) == 1
    assert stored_bets[0].payout == 20
    with pytest.raises(RuntimeError):
        session.save_pending_round()


def test_round_transaction_rolls_back_partial_bets_and_balance(initialized_db, monkeypatch):
    profile = PlayerRepository().add_player("Rollback")
    session = create_game_session(profile.id)
    session.game.place_bets([Bet(5, BetType.RED), Bet(10, BetType.RED)])
    monkeypatch.setattr(session.game.wheel, "spin", lambda: session.game.wheel.pockets[1])
    with database.get_connection() as conn:
        conn.execute("""CREATE TRIGGER fail_second_bet BEFORE INSERT ON round_bets
                        WHEN NEW.amount = 10 BEGIN SELECT RAISE(ABORT, 'test failure'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        session.spin_and_save()
    assert session.has_pending_round
    with database.get_connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM rounds").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM round_bets").fetchone()[0] == 0
        assert conn.execute("SELECT balance FROM players WHERE id = ?", (profile.id,)).fetchone()[0] == 1000
        conn.execute("DROP TRIGGER fail_second_bet")
    result = session.save_pending_round()
    assert result.total_stake == 15
    assert len(RoundRepository().get_player_rounds(profile.id)) == 1
    assert len(RoundRepository().get_player_bets(profile.id)) == 2
    assert PlayerRepository().get_player(profile.id).balance == 1015


def test_schema_is_idempotent_and_foreign_keys_are_enabled(initialized_db):
    profile = PlayerRepository().add_player("Schema")
    database.init_db()
    assert PlayerRepository().get_player(profile.id) == profile
    with database.get_connection() as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"players", "rounds", "round_bets", "player_badges"} <= tables
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def load_database_copy():
    spec = importlib.util.spec_from_file_location("database_path_probe", database.__file__)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_database_path_is_independent_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module = load_database_copy()
    assert module.DB_PATH == Path(database.__file__).resolve().parents[2] / "data/roulette.db"
    assert not (tmp_path / "data").exists()


def test_frozen_database_bootstrap_preserves_existing_file(tmp_path, monkeypatch):
    executable = tmp_path / "portable/ObsidianRoyaleGUI.exe"
    bundle = tmp_path / "bundle"
    demo = bundle / "demo/roulette.db"
    demo.parent.mkdir(parents=True)
    with sqlite3.connect(demo) as conn:
        conn.execute("CREATE TABLE marker (value TEXT)")
        conn.execute("INSERT INTO marker VALUES ('demo')")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable))
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    module = load_database_copy()
    assert module.DB_PATH == executable.parent / "data/roulette.db"
    module.init_db()
    with module.get_connection() as conn:
        assert conn.execute("SELECT value FROM marker").fetchone()[0] == "demo"
        conn.execute("UPDATE marker SET value = 'user progress'")
    module.init_db()
    with module.get_connection() as conn:
        assert conn.execute("SELECT value FROM marker").fetchone()[0] == "user progress"
