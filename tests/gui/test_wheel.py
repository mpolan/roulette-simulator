"""Celowane kontrole koła, zapisu i blokad Etapu 4."""

from threading import Event

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QTimer

from domain.bet import Bet, BetType
from domain.round_result import RoundResult
from domain.wheel import Wheel
from gui.application import create_application
from gui.main_window import MainWindow
from gui.widgets.roulette_wheel import RouletteWheel
from persistence.player_repository import PlayerRepository
from persistence.round_repository import RoundRepository


@pytest.fixture
def round_window(qapp, initialized_db, wait_until):
    create_application([])
    player = PlayerRepository().add_player("Koło test")
    window = MainWindow()
    window.show()
    window.controller.select_profile(player.id)
    wait_until(lambda: window.controller.session is not None)
    window.show_game()
    window.game_view.wheel.duration_ms = 80
    yield window
    wait_until(lambda: not window.controller.busy and not window.controller.animating)
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


def test_all_pockets_align_with_pointer(qapp):
    wheel = RouletteWheel()
    pockets = Wheel().pockets
    wheel.set_pockets(pockets)
    assert wheel.pockets == pockets
    assert {p.number for p in wheel.pockets} == set(range(37))
    for pocket in pockets:
        wheel.rotation = wheel.target_rotation(pocket)
        assert wheel.number_at_pointer() == pocket.number
    wheel.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_animation_emits_exact_result_and_reset_stops(qapp, wait_until):
    wheel = RouletteWheel()
    wheel.set_pockets(Wheel().pockets)
    wheel.duration_ms = 40
    result = RoundResult(wheel.pockets[17], (), 0, 0, 0)
    finished = []
    wheel.animation_finished.connect(finished.append)
    wheel.start(result)
    wait_until(lambda: bool(finished))
    assert finished == [result] and finished[0] is result
    assert wheel.number_at_pointer() == result.pocket.number
    wheel.start(result)
    wheel.reset()
    assert not wheel.animating and wheel.result is None
    assert wheel.animation.state() == wheel.animation.State.Stopped
    wheel.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_spin_persists_settlement_and_blocks_animation(round_window, monkeypatch, wait_until):
    window = round_window
    control, view = window.game_controller, window.game_view
    session = control.session
    calls = []
    pocket = session.game.wheel.pockets[0]
    monkeypatch.setattr(session.game.wheel, "spin", lambda: calls.append(1) or pocket)
    session.game.place_bets([Bet(10, BetType.STRAIGHT, 0), Bet(10, BetType.RED)])
    control.refresh()
    view.wheel.duration_ms = 250
    assert control.spin()
    assert not control.spin()
    wait_until(lambda: control.animating)
    assert window.controller.navigation_blocked()
    assert not view.table.isEnabled() and not view.spin_button.isEnabled()
    assert not control.activate_field(BetType.RED)
    assert not control.set_mode("CLASSIC")
    window.show_menu()
    assert window.stack.currentWidget() is view
    wait_until(lambda: not control.animating)
    result = control.result
    assert calls == [1]
    assert (result.total_stake, result.total_payout, result.net_profit) == (20, 360, 340)
    assert session.game.player.balance == 1340
    stored = RoundRepository().get_player_rounds(session.player_id)
    assert len(stored) == 1 and stored[0].winning_number == 0
    assert view.wheel.number_at_pointer() == 0
    assert "ZIELONE" in view.result_title.text()
    assert "WYGRANY" in view.result_bets.item(0).text()
    assert "PRZEGRANY" in view.result_bets.item(1).text()
    assert "+340$" in view.result_summary.text()
    view.next_button.click()
    assert view.body.currentWidget() is view.betting_page
    assert control.activate_field(BetType.BLACK)


def test_failed_save_retry_reuses_result_and_gui_stays_responsive(round_window, monkeypatch, wait_until):
    window = round_window
    control, view = window.game_controller, window.game_view
    session = control.session
    calls, results, ticks = [], [], []
    entered, release = Event(), Event()
    original = RoundRepository.save_round

    def save(repository, player_id, result, balance_after):
        results.append(result)
        if len(results) == 1:
            entered.set()
            if not release.wait(3):
                raise RuntimeError("Test nie zwolnił zapisu")
            raise OSError("Testowa awaria zapisu")
        return original(repository, player_id, result, balance_after)

    monkeypatch.setattr(RoundRepository, "save_round", save)
    monkeypatch.setattr(session.game.wheel, "spin", lambda: calls.append(1) or session.game.wheel.pockets[1])
    control.activate_field(BetType.RED)
    timer = QTimer(view)
    timer.setInterval(5)
    timer.timeout.connect(lambda: ticks.append(1))
    timer.start()
    try:
        assert control.spin()
        wait_until(lambda: entered.is_set() and len(ticks) >= 2)
        assert window.controller.busy
        assert not control.spin() and not control.retry_save()
    finally:
        release.set()
        timer.stop()
    wait_until(lambda: not window.controller.busy)
    assert session.has_pending_round and control.result is None
    assert view.retry_button.isVisible() and view.retry_button.isEnabled()
    assert not control.activate_field(BetType.BLACK) and not control.spin()
    assert window.controller.navigation_blocked()
    assert control.retry_save()
    wait_until(lambda: control.result is not None and not control.animating)
    assert len(results) == 2 and results[0] is results[1] is control.result
    assert calls == [1] and not session.has_pending_round
    assert len(RoundRepository().get_player_rounds(session.player_id)) == 1


def test_profile_change_clears_previous_wheel_result(round_window, wait_until):
    window = round_window
    control, view = window.game_controller, window.game_view
    control.activate_field(BetType.RED)
    control.spin()
    wait_until(lambda: control.result is not None and not control.animating)
    previous = control.session
    player = PlayerRepository().add_player("Nowe koło")
    assert window.controller.select_profile(player.id)
    wait_until(lambda: control.session is not previous)
    assert control.result is None and view.wheel.result is None
    assert view.result_bets.count() == 0
    assert view.body.currentWidget() is view.betting_page
