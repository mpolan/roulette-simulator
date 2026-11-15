"""Celowane testy widoku statystyk i integracji z istniejącymi usługami."""

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QTest

from domain.bet import Bet, BetType
from gui.application import create_application
from gui.main_window import MainWindow
from persistence.player_repository import PlayerRepository
from persistence.shop_repository import ShopRepository
from services.shop_service import ShopService
from services.stats_service import StatsService


@pytest.fixture
def window(qapp, initialized_db, wait_until):
    create_application([])
    player = PlayerRepository().add_player("Statystyki", 10000)
    window = MainWindow()
    window.show()
    window.controller.select_profile(player.id)
    wait_until(lambda: window.controller.session is not None)
    yield window
    wait_until(lambda: not window.controller.busy)
    session = window.controller.session
    for bet in session.game.current_bets:
        session.game.remove_bet(bet)
    if session.has_pending_round:
        session.save_pending_round()
    window.close()
    wait_until(lambda: not window.isVisible())
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def open_statistics(window, wait_until):
    QTest.mouseClick(window.menu_view.statistics_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    assert window.stack.currentWidget() is window.statistics_view


def test_empty_profile_and_refresh_keep_existing_widgets(window, wait_until):
    open_statistics(window, wait_until)
    view = window.statistics_view
    assert view.player_label.text() == "Statystyki"
    assert view.balance_label.text() == "10000$"
    assert view.values["total_rounds"].text() == "0"
    assert view.values["total_stake"].text() == "0$"
    assert view.values["win_rate"].text() == "0.00%"
    assert view.values["bet_win_rate"].text() == "0.00%"
    assert view.no_rounds_label.isVisible()
    assert "pusta" in view.badge_collection.empty_label.text()
    assert view.badge_collection.empty_label.isVisible()
    assert view.badge_count_label.text() == "Posiadane: 0"
    assert view.spent_label.text() == "Wydano w sklepie: 0$"
    old_label = view.values["total_rounds"]
    QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    assert view.values["total_rounds"] is old_label
    QTest.keyClick(view.refresh_button, Qt.Key.Key_Escape)
    assert window.stack.currentWidget() is window.menu_view


def test_saved_statistics_badges_and_balance_with_active_bet(window, wait_until, monkeypatch):
    session = window.controller.session
    pocket = next(p for p in session.game.wheel.pockets if p.number == 32)
    monkeypatch.setattr(session.game.wheel, "spin", lambda: pocket)
    session.game.place_bet(Bet(10, BetType.RED))
    session.spin_and_save()
    ShopService(ShopRepository()).buy_badge(session, "bronze_roller")
    saved_balance = session.game.player.balance
    session.game.place_chip(BetType.BLACK, 25)
    window.game_controller.refresh()
    open_statistics(window, wait_until)
    view = window.statistics_view
    assert view.balance_label.text() == f"{saved_balance}$"
    assert session.game.player.balance == saved_balance - 25
    assert {key: view.values[key].text() for key in view.values} == {
        "total_rounds": "1", "profitable_rounds": "1", "total_bets": "1", "winning_bets": "1",
        "total_stake": "10$", "total_payout": "20$", "net_profit": "+10$", "biggest_payout": "20$",
        "win_rate": "100.00%", "bet_win_rate": "100.00%",
    }
    assert not view.no_rounds_label.isVisible()
    assert view.badge_count_label.text() == "Posiadane: 1"
    assert view.spent_label.text() == "Wydano w sklepie: 2500$"
    assert view.badge_collection.list_widget.count() == 1
    assert "☻" in view.badge_collection.list_widget.item(0).text()
    assert "Bronze Roller" in view.badge_collection.list_widget.item(0).text()
    assert session.game.current_bets[0].amount == 25


def test_read_error_preserves_data_and_refresh_recovers(window, wait_until, monkeypatch):
    open_statistics(window, wait_until)
    view = window.statistics_view
    previous = view.balance_label.text()
    with monkeypatch.context() as patch:
        def fail(*args):
            raise OSError("testowy błąd odczytu")
        patch.setattr(StatsService, "get_player_stats", fail)
        QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
        wait_until(lambda: not window.controller.busy)
        assert "Nie można odczytać statystyk" in view.message.text()
        assert view.balance_label.text() == previous
        assert view.refresh_button.isEnabled()
    QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    assert not view.message.text()
    assert view.balance_label.text() == previous


def test_switch_profile_clears_previous_statistics(window, wait_until):
    open_statistics(window, wait_until)
    view = window.statistics_view
    other = PlayerRepository().add_player("Nowy profil", 2345)
    assert window.controller.select_profile(other.id)
    wait_until(lambda: window.controller.session.player_id == other.id)
    assert view.player_label.text() == "—"
    assert view.balance_label.text() == "—"
    open_statistics(window, wait_until)
    assert window.statistics_view is view
    assert view.player_label.text() == "Nowy profil"
    assert view.balance_label.text() == "2345$"
    assert view.values["total_rounds"].text() == "0"
