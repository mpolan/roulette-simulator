"""Grupowanie prezentacji bez zmiany oryginalnych zakładów i rozliczenia."""

from unittest.mock import Mock

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QTest

from domain.bet import Bet, BetType
from domain.game import Game
from domain.player import Player
from gui.application import create_application
from gui.controllers.game_controller import GameController
from gui.views.game import GameView
from services.game_session import GameSession


@pytest.fixture
def view(qapp):
    create_application([])
    controller = GameController()
    controller.set_session(GameSession(1, Game(Player("Grupy", 1000)), Mock()))
    widget = GameView(controller)
    widget.resize(900, 620)
    widget.show()
    yield widget
    widget.close()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_cart_groups_amounts_but_removes_one_original_bet_lifo(view):
    controller = view.controller
    game = controller.session.game
    first, equal, larger = (Bet(10, BetType.DOZEN, 1), Bet(10, BetType.DOZEN, 1),
                            Bet(25, BetType.DOZEN, 1))
    game.place_bets([first, equal, larger, Bet(5, BetType.RED)])
    game.place_chip(BetType.DOZEN, 50, 1)
    chip = game.current_bets[-1]
    controller.refresh()
    cart = view.cart
    assert cart.count() == 2
    group = cart.rows[id(first)]
    assert cart.rows[id(equal)] is group and cart.rows[id(chip)] is group
    assert group.text() == "DOZEN 1 · zakładów: 4 · 95$"
    assert "jeden ostatni" in group.toolTip()
    cart.setCurrentItem(group)
    removed = []
    cart.remove_requested.connect(removed.append)
    QTest.keyClick(cart, Qt.Key.Key_Delete)
    assert removed[-1] is chip
    assert game.player.balance == 950
    assert (BetType.DOZEN, 1) not in game.chip_stacks
    assert cart.rows[id(first)] is group
    assert group.text() == "DOZEN 1 · zakładów: 3 · 45$"
    cart.remove_current()
    assert removed[-1] is larger
    cart.remove_current()
    assert removed[-1] is equal
    assert game.current_bets[0] is first
    assert game.player.balance == 985
    assert cart.rows[id(first)] is group
    assert id(equal) not in cart.rows and id(chip) not in cart.rows
    assert group.text() == "DOZEN 1 · zakładów: 1 · 10$"


def test_spin_result_groups_ready_bet_results_without_changing_totals(view, monkeypatch):
    session = view.controller.session
    game = session.game
    pocket = next(p for p in game.wheel.pockets if p.number == 1)
    monkeypatch.setattr(game.wheel, "spin", lambda: pocket)
    game.place_bets([Bet(10, BetType.DOZEN, 1), Bet(25, BetType.DOZEN, 1),
                     Bet(5, BetType.BLACK), Bet(10, BetType.BLACK)])
    result = session.spin_and_save()
    original_results = result.bet_results
    view.reveal_result(result)
    assert len(original_results) == 4
    assert result.bet_results is original_results
    assert view.result_bets.count() == 2
    assert view.result_bets.item(0).text() == "WYGRANY · DOZEN 1 · zakładów: 2\nStawka 35$ · wypłata 105$"
    assert view.result_bets.item(1).text() == "PRZEGRANY · BLACK · zakładów: 2\nStawka 15$ · wypłata 0$"
    assert (result.total_stake, result.total_payout, result.net_profit) == (50, 105, 55)
    assert "Stawka: 50$" in view.result_summary.text()
    assert "Wypłata: 105$" in view.result_summary.text()
    assert "Bilans rundy: +55$" in view.result_summary.text()
