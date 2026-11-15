"""Kontrakty statystyk, rankingu i sklepu na istniejących repozytoriach."""

import sqlite3

import pytest

from domain.badge import Badge
from domain.bet import Bet, BetType
from domain.game import Game
from domain.player import Player
from persistence import database
from persistence.player_repository import PlayerRepository
from persistence.round_repository import RoundRepository
from persistence.shop_repository import ShopRepository
from services.game_session import GameSession
from services.leaderboard_service import LeaderboardService
from services.session_factory import create_game_session
from services.shop_service import ShopService
from services.stats_service import StatsService


def save_fixed_round(session, bets, number, monkeypatch):
    pocket = next(p for p in session.game.wheel.pockets if p.number == number)
    monkeypatch.setattr(session.game.wheel, "spin", lambda: pocket)
    session.game.place_bets(bets)
    return session.spin_and_save()


def test_statistics_distinguish_profitable_rounds_from_winning_bets(initialized_db, monkeypatch):
    player = PlayerRepository().add_player("Statystyki")
    service = StatsService(RoundRepository())
    empty = service.get_player_stats(player.id)
    assert empty.total_rounds == empty.total_bets == 0
    assert empty.win_rate == empty.bet_win_rate == 0
    assert empty.biggest_payout == empty.net_profit == 0
    session = create_game_session(player.id)
    save_fixed_round(session, [Bet(10, BetType.RED), Bet(20, BetType.BLACK)], 1, monkeypatch)
    save_fixed_round(session, [Bet(10, BetType.RED), Bet(10, BetType.BLACK)], 1, monkeypatch)
    save_fixed_round(session, [Bet(5, BetType.STRAIGHT, 0)], 0, monkeypatch)
    stats = service.get_player_stats(player.id)
    assert stats.total_rounds == 3
    assert stats.profitable_rounds == 1
    assert stats.total_bets == 5
    assert stats.winning_bets == 3
    assert stats.total_stake == 55
    assert stats.total_payout == 220
    assert stats.net_profit == 165
    assert stats.biggest_payout == 180
    assert stats.win_rate == pytest.approx(100 / 3)
    assert stats.bet_win_rate == 60
    assert PlayerRepository().get_player(player.id).balance == 1165


def test_leaderboard_sorting_thresholds_ties_and_badges(initialized_db, monkeypatch):
    players = PlayerRepository()
    shop = ShopService(ShopRepository())
    leaderboard = LeaderboardService(players, StatsService(RoundRepository()), shop)
    assert leaderboard.get_leaderboard() == []
    alpha = players.add_player("Alfa", 20000)
    beta = players.add_player("Beta", 20000)
    novice = players.add_player("Dziewięć rund", 20000)
    collector = players.add_player("Kolekcjoner", 20000)
    players.add_player("Bez aktywności")
    for profile, count in ((alpha, 10), (beta, 10), (novice, 9)):
        session = create_game_session(profile.id)
        for index in range(count):
            number = 1 if profile.id == novice.id or index < 5 else 2
            save_fixed_round(session, [Bet(10, BetType.RED)], number, monkeypatch)
    shop.buy_badge(create_game_session(alpha.id), "bronze_roller")
    collection_session = create_game_session(collector.id)
    shop.buy_badge(collection_session, "bronze_roller")
    shop.buy_badge(collection_session, "silver_roller")
    expected = {
        "net_profit": [novice.id, alpha.id, beta.id],
        "total_rounds": [alpha.id, beta.id, novice.id],
        "win_rate": [alpha.id, beta.id],
        "badge_count": [collector.id, alpha.id],
    }
    assert set(leaderboard.SORT_FIELDS) == set(expected)
    for sort_by, ids in expected.items():
        entries = leaderboard.get_leaderboard(sort_by)
        assert [entry.player_id for entry in entries] == ids
        for entry in entries:
            assert entry.balance == players.get_player(entry.player_id).balance
    assert leaderboard.get_leaderboard("badge_count")[0].badge_count == 2
    with pytest.raises(ValueError):
        leaderboard.get_leaderboard("balance")


def test_purchase_updates_database_session_and_collection(initialized_db):
    profile = PlayerRepository().add_player("Kupujący", 10000)
    session = create_game_session(profile.id)
    shop = ShopService(ShopRepository())
    assert len(shop.get_catalog()) == 5
    assert shop.get_owned_badges(profile.id) == []
    purchase = shop.buy_badge(session, "bronze_roller")
    assert purchase.player_id == profile.id
    assert purchase.badge_id == "bronze_roller"
    assert purchase.price_paid == 2500
    assert session.game.player.balance == 7500
    assert PlayerRepository().get_player(profile.id).balance == 7500
    assert [badge.id for badge in shop.get_owned_badges(profile.id)] == ["bronze_roller"]
    assert shop.get_total_spent(profile.id) == 2500
    with pytest.raises(ValueError):
        shop.buy_badge(session, "bronze_roller")
    with pytest.raises(ValueError):
        shop.buy_badge(session, "unknown")
    assert session.game.player.balance == 7500
    assert len(ShopRepository().get_player_badges(profile.id)) == 1


def test_purchase_rejections_do_not_change_balances(initialized_db, monkeypatch):
    profile = PlayerRepository().add_player("Ograniczenia", 10000)
    session = create_game_session(profile.id)
    shop = ShopService(ShopRepository())
    session.game.place_bet(Bet(5, BetType.RED))
    with pytest.raises(RuntimeError):
        shop.buy_badge(session, "bronze_roller")
    assert session.game.player.balance == 9995
    session.game.remove_bet(session.game.current_bets[0])

    def fail_save(*args, **kwargs):
        raise sqlite3.OperationalError("simulated storage failure")

    monkeypatch.setattr(RoundRepository, "save_round", fail_save)
    monkeypatch.setattr(session.game.wheel, "spin", lambda: session.game.wheel.pockets[0])
    session.game.place_bet(Bet(5, BetType.RED))
    with pytest.raises(sqlite3.OperationalError):
        session.spin_and_save()
    with pytest.raises(RuntimeError):
        shop.buy_badge(session, "bronze_roller")
    assert session.has_pending_round
    assert session.game.player.balance == 9995
    assert PlayerRepository().get_player(profile.id).balance == 10000
    assert shop.get_owned_badges(profile.id) == []
    poor = PlayerRepository().add_player("Brak środków")
    poor_session = create_game_session(poor.id)
    with pytest.raises(ValueError):
        shop.buy_badge(poor_session, "bronze_roller")
    assert poor_session.game.player.balance == 1000
    assert PlayerRepository().get_player(poor.id).balance == 1000
    missing = GameSession(-1, Game(Player(balance=10000)), RoundRepository())
    with pytest.raises(LookupError):
        shop.buy_badge(missing, "bronze_roller")
    assert missing.game.player.balance == 10000


def test_purchase_transaction_rolls_back_debit_on_insert_failure(initialized_db):
    profile = PlayerRepository().add_player("Rollback sklepu", 10000)
    session = create_game_session(profile.id)
    shop = ShopService(ShopRepository())
    with database.get_connection() as conn:
        conn.execute("""CREATE TRIGGER fail_purchase BEFORE INSERT ON player_badges
                        BEGIN SELECT RAISE(ABORT, 'test failure'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        shop.buy_badge(session, "bronze_roller")
    assert session.game.player.balance == 10000
    assert PlayerRepository().get_player(profile.id).balance == 10000
    assert shop.get_owned_badges(profile.id) == []


@pytest.mark.parametrize("price", [0, -1, True, 2.5])
def test_repository_rejects_invalid_badge_price(initialized_db, price):
    profile = PlayerRepository().add_player("Cena", 10000)
    with pytest.raises(ValueError):
        ShopRepository().purchase_badge(profile.id, Badge("invalid", "Test", price, "?", "Test"))
    assert PlayerRepository().get_player(profile.id).balance == 10000


def test_unknown_stored_badge_is_hidden_but_its_cost_is_preserved(initialized_db):
    profile = PlayerRepository().add_player("Starszy katalog", 10000)
    ShopRepository().purchase_badge(profile.id, Badge("old_badge", "Stara", 100, "?", "Stara"))
    shop = ShopService(ShopRepository())
    assert shop.get_owned_badges(profile.id) == []
    assert shop.get_total_spent(profile.id) == 100
