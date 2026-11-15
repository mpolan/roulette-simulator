"""Celowane testy sklepu przez GUI i istniejące usługi na tymczasowej bazie."""

import sqlite3

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QTest

from domain.bet import Bet, BetType
from gui.application import create_application
from gui.main_window import MainWindow
from persistence.player_repository import PlayerRepository
from persistence.round_repository import RoundRepository
from persistence.shop_repository import ShopRepository
from services.shop_service import ShopService


@pytest.fixture
def window(qapp, initialized_db, wait_until):
    create_application([])
    player = PlayerRepository().add_player("Gracz sklepu", 10000)
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
    window.controller.animating = False
    window.close()
    wait_until(lambda: not window.isVisible())
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def open_shop(window, wait_until):
    QTest.mouseClick(window.menu_view.shop_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    assert window.stack.currentWidget() is window.shop_view
    return window.shop_view


def test_purchase_persists_once_and_appears_in_statistics_and_ranking(window, wait_until):
    view = open_shop(window, wait_until)
    session = window.controller.session
    assert len(view.cards) == len(ShopService(ShopRepository()).get_catalog()) == 5
    assert view.player_label.text() == "Gracz sklepu"
    assert view.balance_label.text() == "10000$"
    card = view.cards["bronze_roller"]
    assert card.symbol_label.text() == "☻"
    assert card.price_label.text() == "2500$"
    card.buy_button.setFocus()
    QTest.keyClick(card.buy_button, Qt.Key.Key_Return)
    assert window.controller.busy
    assert not window.controller.buy_badge("bronze_roller")
    wait_until(lambda: not window.controller.busy)
    assert view.cards["bronze_roller"] is card
    assert card.state_label.text() == "POSIADANA"
    assert not card.buy_button.isEnabled()
    assert "Kupiono Bronze Roller" in view.message.text()
    assert session.game.player.balance == 7500
    assert PlayerRepository().get_player(session.player_id).balance == 7500
    assert len(ShopRepository().get_player_badges(session.player_id)) == 1
    assert "7500" in window.menu_view.balance_label.text()

    QTest.keyClick(view.refresh_button, Qt.Key.Key_Escape)
    assert window.stack.currentWidget() is window.menu_view
    QTest.mouseClick(window.menu_view.statistics_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    stats = window.statistics_view
    assert stats.balance_label.text() == "7500$"
    assert stats.badge_count_label.text() == "Posiadane: 1"
    assert "Bronze Roller" in stats.badge_collection.list_widget.item(0).text()
    window.show_menu()
    window.show_leaderboard()
    wait_until(lambda: not window.controller.busy)
    ranking = window.leaderboard
    ranking.sort_combo.setCurrentIndex(ranking.sort_combo.findData("badge_count"))
    wait_until(lambda: not window.controller.busy)
    assert "☻ Gracz sklepu (Ty)" == ranking.table.item(0, 1).text()
    assert ranking.table.item(0, 5).text() == "1"


def test_insufficient_funds_and_duplicate_are_rejected(window, wait_until):
    view = open_shop(window, wait_until)
    session = window.controller.session
    expensive = view.cards["casino_roller"]
    assert not expensive.buy_button.isEnabled()
    assert "Brakuje" in expensive.state_label.text()
    assert window.controller.buy_badge("casino_roller")
    wait_until(lambda: not window.controller.busy)
    assert "wystarczających środków" in view.message.text()
    assert PlayerRepository().get_player(session.player_id).balance == 10000
    QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    QTest.mouseClick(view.cards["bronze_roller"].buy_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    assert window.controller.buy_badge("bronze_roller")
    wait_until(lambda: not window.controller.busy)
    assert "już w Twojej kolekcji" in view.message.text()
    assert session.game.player.balance == 7500
    assert len(ShopRepository().get_player_badges(session.player_id)) == 1


def test_active_bets_pending_and_animation_block_purchase(window, wait_until, monkeypatch):
    session = window.controller.session
    bet = Bet(10, BetType.RED)
    session.game.place_bet(bet)
    window.game_controller.refresh()
    view = open_shop(window, wait_until)
    assert "aktywne zakłady" in view.reason_label.text()
    assert not view.cards["bronze_roller"].buy_button.isEnabled()
    assert view.back_button.isEnabled()
    assert not window.controller.buy_badge("bronze_roller")
    assert session.game.player.balance == 9990
    session.game.remove_bet(bet)
    window.game_controller.refresh()
    assert view.cards["bronze_roller"].buy_button.isEnabled()

    session.game.place_bet(Bet(10, BetType.RED))
    with monkeypatch.context() as patch:
        def fail(*args, **kwargs):
            raise sqlite3.OperationalError("test pending")
        patch.setattr(RoundRepository, "save_round", fail)
        with pytest.raises(sqlite3.OperationalError):
            session.spin_and_save()
    window.game_controller.refresh()
    assert session.has_pending_round
    assert not window.controller.buy_badge("bronze_roller")
    assert not view.back_button.isEnabled()
    assert "ponów zapis" in view.reason_label.text()
    session.save_pending_round()
    window.controller.animating = True
    window.game_controller.refresh()
    assert not window.controller.buy_badge("bronze_roller")
    assert not view.cards["bronze_roller"].buy_button.isEnabled()
    window.controller.animating = False
    window.game_controller.refresh()
    assert ShopRepository().get_player_badges(session.player_id) == []


def test_read_and_purchase_error_recover_after_refresh_and_profile_switch(window, wait_until, monkeypatch):
    view = open_shop(window, wait_until)
    card = view.cards["bronze_roller"]
    with monkeypatch.context() as patch:
        def fail(*args):
            raise OSError("testowy błąd")
        patch.setattr(ShopService, "get_owned_badges", fail)
        QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
        wait_until(lambda: not window.controller.busy)
        assert "Nie można odczytać" in view.message.text()
        assert not card.buy_button.isEnabled()
    QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    assert view.cards["bronze_roller"] is card
    assert card.buy_button.isEnabled()
    assert not view.message.text()
    with monkeypatch.context() as patch:
        def fail(*args):
            raise OSError("test zakupu")
        patch.setattr(ShopService, "buy_badge", fail)
        QTest.mouseClick(card.buy_button, Qt.MouseButton.LeftButton)
        wait_until(lambda: not window.controller.busy)
        assert "Nie udało się kupić" in view.message.text()
        assert not card.buy_button.isEnabled()
        assert window.controller.session.game.player.balance == 10000
    QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    assert card.buy_button.isEnabled()
    other = PlayerRepository().add_player("Drugi", 1200)
    assert window.controller.select_profile(other.id)
    wait_until(lambda: window.controller.session.player_id == other.id)
    assert view.player_label.text() == "—"
    open_shop(window, wait_until)
    assert view.player_label.text() == "Drugi"
    assert view.balance_label.text() == "1200$"
    assert not card.buy_button.isEnabled()
