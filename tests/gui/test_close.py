"""Potwierdzenie zamknięcia: zwroty przez Game i ochrona pending."""

import sqlite3
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox

from domain.bet import Bet, BetType
from gui.application import create_application
from gui.main_window import MainWindow
from persistence.player_repository import PlayerRepository
from persistence.round_repository import RoundRepository


@pytest.fixture
def window(qapp, initialized_db, wait_until):
    create_application([])
    player = PlayerRepository().add_player("Zamykanie")
    result = MainWindow()
    result.show()
    result.activateWindow()
    result.start()
    wait_until(lambda: not result.controller.busy)
    result.controller.select_profile(player.id)
    wait_until(lambda: result.controller.session is not None)
    yield result
    if result._close_dialog is not None:
        result._close_dialog.reject()
    result.controller.busy = False
    result.controller.animating = False
    session = result.controller.session
    if session is not None:
        for bet in session.game.current_bets:
            session.game.remove_bet(bet)
        if session.has_pending_round:
            session.save_pending_round()
    result.close()
    wait_until(lambda: not result.isVisible())
    # close() ukrywa okno. Usuń jego graf QObject w wątku GUI, zanim
    # cykliczny GC kolejnego testu uruchomi się w workerze profili.
    result.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def add_bets(window):
    game = window.controller.session.game
    game.place_chip(BetType.RED, 25)
    game.place_bets([Bet(25, BetType.RED), Bet(25, BetType.RED)])
    window.game_controller.refresh()
    return game.current_bets


def confirm(dialog):
    button = next(button for button in dialog.buttons()
                  if dialog.buttonRole(button) == QMessageBox.ButtonRole.DestructiveRole)
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)


def make_pending(session, monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(session.game.wheel, "spin", lambda: session.game.wheel.pockets[0])
        patch.setattr(RoundRepository, "save_round", Mock(side_effect=sqlite3.OperationalError("dysk")))
        with pytest.raises(sqlite3.OperationalError):
            session.spin_and_save()
    assert session.has_pending_round


@pytest.mark.parametrize("has_session", [False, True])
def test_empty_window_closes_without_confirmation(window, wait_until, has_session):
    if not has_session:
        window.controller.session = None
    window.close()
    assert window._close_dialog is None
    wait_until(lambda: not window.isVisible())


def test_confirm_cancels_each_original_bet_and_refunds_before_shutdown(window, monkeypatch, wait_until):
    bets = add_bets(window)
    session = window.controller.session
    game = session.game
    remove = Mock(wraps=game.remove_bet)
    monkeypatch.setattr(game, "remove_bet", remove)
    monkeypatch.setattr(session, "spin_and_save", Mock(side_effect=AssertionError("spin forbidden")))
    monkeypatch.setattr(session, "save_pending_round", Mock(side_effect=AssertionError("save forbidden")))
    stopped = []
    window.controller.shutdown_finished.connect(lambda: stopped.append(True))
    window.close()  # Ten sam closeEvent co systemowy X.
    dialog = window._close_dialog
    assert dialog is not None and window.isVisible()
    assert game.player.balance == 925 and len(game.current_bets) == 3
    confirm(dialog)
    wait_until(lambda: not window.isVisible())
    assert len(remove.call_args_list) == 3
    assert all(call.args[0] is bet for call, bet in zip(remove.call_args_list, bets))
    assert game.current_bets == () and game.chip_stacks == {}
    assert game.player.balance == 1000
    assert PlayerRepository().get_player(session.player_id).balance == 1000
    session.spin_and_save.assert_not_called()
    session.save_pending_round.assert_not_called()
    assert stopped == [True]


@pytest.mark.parametrize("decision", ["button", "escape", "enter", "dialog_x"])
def test_return_preserves_bets_and_session(window, qapp, decision):
    bets = add_bets(window)
    session = window.controller.session
    window.show_menu()
    window.close()
    dialog = window._close_dialog
    back = dialog.defaultButton()
    assert back.text() == "Wróć do gry"
    assert dialog.escapeButton() is back
    qapp.processEvents()
    if decision == "button":
        QTest.mouseClick(back, Qt.MouseButton.LeftButton)
    elif decision == "escape":
        QTest.keyClick(dialog, Qt.Key.Key_Escape)
    elif decision == "enter":
        back.setFocus()
        QTest.keyClick(back, Qt.Key.Key_Return)
    else:
        dialog.close()
    qapp.processEvents()
    assert window._close_dialog is None
    assert window.isVisible()
    assert window.stack.currentWidget() is window.game_view
    assert window.controller.session is session
    assert all(active is bet for active, bet in zip(session.game.current_bets, bets))
    assert session.game.player.balance == 925
    assert session.game.chip_stacks[(BetType.RED, None)][0] is bets[0]


def test_repeated_close_keeps_one_nonblocking_dialog(window, qapp, wait_until):
    add_bets(window)
    window.close()
    dialog = window._close_dialog
    ticks = []
    QTimer.singleShot(0, lambda: ticks.append(True))
    window.close()
    wait_until(lambda: ticks)
    assert window._close_dialog is dialog
    assert len([d for d in window.findChildren(QMessageBox) if d.isVisible()]) == 1
    assert window.controller.session.game.total_stake == 75


@pytest.mark.parametrize("trigger", ["alt_f4", "ctrl_q", "exit_button"])
def test_close_shortcuts_and_exit_button_use_confirmation(window, qapp, trigger):
    add_bets(window)
    window.show_menu()
    window.activateWindow()
    qapp.processEvents()
    if trigger == "exit_button":
        assert window.menu_view.exit_button.isEnabled()
        QTest.mouseClick(window.menu_view.exit_button, Qt.MouseButton.LeftButton)
    else:
        key, modifier = ((Qt.Key.Key_F4, Qt.KeyboardModifier.AltModifier) if trigger == "alt_f4"
                         else (Qt.Key.Key_Q, Qt.KeyboardModifier.ControlModifier))
        QTest.keyClick(window.menu_view.game_button, key, modifier)
    qapp.processEvents()
    assert window._close_dialog is not None
    assert window.controller.session.game.total_stake == 75


def test_pending_blocks_close_and_cancel_even_with_active_bet(window, monkeypatch, qapp):
    session = window.controller.session
    add_bets(window)
    make_pending(session, monkeypatch)
    # Game nie blokuje mutacji pending: kontroler musi chronić także taki stan.
    session.game.place_bet(Bet(5, BetType.BLACK))
    active = session.game.current_bets[0]
    balance = session.game.player.balance
    window.close()
    qapp.processEvents()
    assert window._close_dialog is None and window.isVisible()
    assert "ponów zapis" in window.statusBar().currentMessage()
    assert not window.controller.shutdown(cancel_bets=True)
    assert session.game.current_bets[0] is active
    assert session.game.player.balance == balance


def test_confirmation_rechecks_pending_before_cancelling(window, monkeypatch, qapp):
    session = window.controller.session
    add_bets(window)
    window.close()
    dialog = window._close_dialog
    make_pending(session, monkeypatch)
    balance = session.game.player.balance
    confirm(dialog)
    qapp.processEvents()
    assert window.isVisible() and session.has_pending_round
    assert session.game.player.balance == balance
    assert "ponów zapis" in window.statusBar().currentMessage()


@pytest.mark.parametrize("lock", ["busy", "animating"])
def test_busy_and_animation_do_not_offer_cancellation(window, lock):
    bets = add_bets(window)
    setattr(window.controller, lock, True)
    window.close()
    assert window._close_dialog is None and window.isVisible()
    assert not window.controller.shutdown(cancel_bets=True)
    assert window.controller.session.game.current_bets == bets
