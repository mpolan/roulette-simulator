"""Stół w trwałym oknie: sesja, nawigacja i dostępność SPIN."""

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QTest

from domain.bet import Bet, BetType
from gui.application import create_application
from gui.main_window import MainWindow
from persistence.player_repository import PlayerRepository


@pytest.fixture
def game_window(qapp, initialized_db, wait_until):
    create_application([])
    player = PlayerRepository().add_player("Stół integracja")
    window = MainWindow()
    window.show()
    window.start()
    wait_until(lambda: not window.controller.busy)
    window.controller.select_profile(player.id)
    wait_until(lambda: window.controller.session is not None)
    yield window
    window.controller.animating = False
    session = window.controller.session
    for bet in session.game.current_bets:
        session.game.remove_bet(bet)
    if session.has_pending_round:
        session.save_pending_round()
    wait_until(lambda: not window.controller.busy)
    window.close()
    wait_until(lambda: not window.isVisible())
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_table_menu_preserves_session_and_updates_balance(game_window):
    window = game_window
    session = window.controller.session
    view = window.game_view
    QTest.mouseClick(window.menu_view.game_button, Qt.MouseButton.LeftButton)
    assert window.stack.currentWidget() is view
    bet = Bet(25, BetType.RED)
    session.game.place_bet(bet)
    window.game_controller.refresh()
    assert "975" in view.balance_label.text()
    assert "975" in window.menu_view.balance_label.text()
    assert not window.menu_view.change_button.isEnabled()
    assert window.menu_view.exit_button.isEnabled()
    QTest.keyClick(view.table, Qt.Key.Key_Escape)
    assert window.stack.currentWidget() is window.menu_view
    assert window.menu_view.game_button.isEnabled()
    QTest.keyClick(window.menu_view.game_button, Qt.Key.Key_Return)
    assert window.stack.currentWidget() is view
    assert window.game_view is view
    assert window.controller.session is session
    assert session.game.current_bets[0] is bet
    window.close()
    assert window.isVisible()
    window._close_dialog.reject()
    session.game.remove_bet(bet)
    window.game_controller.refresh()
    assert window.menu_view.change_button.isEnabled()
    assert "1000" in window.menu_view.balance_label.text()


def test_spin_requires_active_bets(game_window, monkeypatch):
    window = game_window
    session = window.controller.session

    def forbidden(*args):
        pytest.fail("Pusty koszyk nie może uruchomić rundy")

    monkeypatch.setattr(session, "spin_and_save", forbidden)
    monkeypatch.setattr(session.game, "spin", forbidden)
    monkeypatch.setattr(session.game.wheel, "spin", forbidden)
    window.show_game()
    assert not window.game_view.spin_button.isEnabled()
    QTest.mouseClick(window.game_view.spin_button, Qt.MouseButton.LeftButton)
    QTest.keyClick(window.game_view.spin_button, Qt.Key.Key_Space)
    bet = Bet(10, BetType.BLACK)
    session.game.place_bet(bet)
    window.game_controller.refresh()
    assert window.game_view.spin_button.isEnabled()
    assert session.game.current_bets[0] is bet
    assert session.game.player.balance == 990


def test_navigation_animation_and_busy_guards(game_window):
    window = game_window
    window.controller.animating = True
    window.show_game()
    assert window.stack.currentWidget() is window.menu_view
    window.controller.animating = False
    window.show_game()
    assert window.stack.currentWidget() is window.game_view
    window.controller.busy = True
    window.controller.busy_changed.emit(True)
    window.show_menu()
    assert window.stack.currentWidget() is window.game_view
    assert not window.game_view.table.isEnabled()
    window.controller.busy = False
    window.controller.busy_changed.emit(False)
    assert window.game_view.table.isEnabled()
    window.show_menu()
    assert window.stack.currentWidget() is window.menu_view


def test_switch_profile_reuses_view_and_replaces_session(game_window, wait_until):
    window = game_window
    old_session = window.controller.session
    view = window.game_view
    player = PlayerRepository().add_player("Drugi stół", 1234)
    window.show_profiles()
    wait_until(lambda: not window.controller.busy)
    window.controller.select_profile(player.id)
    wait_until(lambda: window.controller.session is not old_session)
    window.show_game()
    assert window.game_view is view
    assert window.stack.count() == 6
    assert window.game_controller.session is window.controller.session
    assert "1234" in view.balance_label.text()
