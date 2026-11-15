"""Integracja profili, blokad sesji i responsywności okna Qt."""

import sqlite3
import threading

import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest

from domain.bet import Bet, BetType
from gui.application import create_application
from gui.controllers.application_controller import ApplicationController
from gui.main_window import MainWindow
from persistence.player_repository import PlayerRepository
from persistence.round_repository import RoundRepository
from services.session_factory import create_game_session


@pytest.fixture
def make_window(qapp, initialized_db, wait_until):
    create_application([])
    windows = []

    def make(controller=None):
        window = MainWindow(controller)
        windows.append(window)
        window.show()
        window.start()
        return window

    yield make
    for window in windows:
        wait_until(lambda: not window.controller.busy, timeout=7000)
        session = window.controller.session
        if session is not None:
            for bet in session.game.current_bets:
                session.game.remove_bet(bet)
            if session.has_pending_round:
                session.save_pending_round()
        window.controller.animating = False
        window.close()
        wait_until(lambda: not window.isVisible())


def select_existing(window, profile_id, wait_until):
    assert window.controller.select_profile(profile_id)
    wait_until(lambda: not window.controller.busy)
    assert window.controller.session.player_id == profile_id


def test_mouse_selection_switching_balance_and_persistent_views(make_window, wait_until):
    players = PlayerRepository()
    first = players.add_player("Pierwszy", 725)
    second = players.add_player("Drugi", 1825)
    window = make_window()
    wait_until(lambda: not window.controller.busy)
    profiles, menu = window.profiles_view, window.menu_view
    assert profiles.profile_list.count() == 2
    profiles.profile_list.setCurrentRow(0)
    QTest.mouseClick(profiles.select_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: window.controller.session is not None)
    assert window.controller.session.player_id == first.id
    assert "Pierwszy" in menu.player_label.text()
    assert "725" in menu.balance_label.text()
    QTest.mouseClick(menu.change_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    profiles.profile_list.setCurrentRow(1)
    QTest.mouseClick(profiles.select_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    assert window.controller.session.player_id == second.id
    assert "1825" in menu.balance_label.text()
    assert window.profiles_view is profiles
    assert window.menu_view is menu
    assert window.stack.count() == 6
    assert len(players.get_all_players()) == 2


def test_invalid_names_never_reach_repository(make_window, wait_until):
    class CountingRepository(PlayerRepository):
        calls = 0

        def add_player(self, name, balance=None):
            self.calls += 1
            return super().add_player(name, balance)

    players = CountingRepository()
    window = make_window(ApplicationController(players=players))
    wait_until(lambda: not window.controller.busy)
    for name in ("", "  ", "a" * 41):
        assert not window.controller.create_profile(name)
        assert window.profiles_view.message.text()
    assert players.calls == 0
    assert window.profiles_view.name_input.maxLength() == 40
    assert players.get_all_players() == []


def test_pending_round_blocks_selection_creation_navigation_and_system_close(make_window, wait_until, monkeypatch, qapp):
    first = PlayerRepository().add_player("Pending")
    second = PlayerRepository().add_player("Drugi")
    window = make_window()
    wait_until(lambda: not window.controller.busy)
    select_existing(window, first.id, wait_until)
    session = window.controller.session
    session.game.place_bet(Bet(5, BetType.RED))

    def fail_save(*args, **kwargs):
        raise sqlite3.OperationalError("test pending")

    with monkeypatch.context() as patch:
        patch.setattr(RoundRepository, "save_round", fail_save)
        with pytest.raises(sqlite3.OperationalError):
            session.spin_and_save()
        assert session.has_pending_round
        assert session.game.current_bets == ()
        assert not window.controller.select_profile(second.id)
        assert not window.controller.create_profile("Niedozwolony")
        window.show_profiles()
        assert window.stack.currentWidget() is window.menu_view
        window.close()
        qapp.processEvents()
        assert window.isVisible()
        assert window.controller.session is session
        assert len(PlayerRepository().get_all_players()) == 2
    session.save_pending_round()
    window.show_profiles()
    wait_until(lambda: not window.controller.busy)
    assert window.stack.currentWidget() is window.profiles_view


def test_io_does_not_block_qt_and_duplicate_requests_are_ignored(make_window, wait_until, qapp):
    entered, release = threading.Event(), threading.Event()
    io_threads = []

    class DelayedRepository(PlayerRepository):
        def add_player(self, name, balance=None):
            io_threads.append(threading.get_ident())
            entered.set()
            if not release.wait(5):
                raise OSError("Test nie zwolnił operacji")
            return super().add_player(name, balance)

    players = DelayedRepository()
    window = make_window(ApplicationController(players=players))
    wait_until(lambda: not window.controller.busy)
    timer = QTimer()
    timer.setInterval(5)
    ticks = []
    timer.timeout.connect(lambda: ticks.append(True))
    timer.start()
    try:
        assert window.controller.create_profile("Jedna operacja")
        wait_until(entered.is_set)
        assert window.controller.busy
        assert not window.controller.create_profile("Druga operacja")
        assert not window.controller.select_profile(999)
        assert not window.controller.load_profiles()
        window.close()
        qapp.processEvents()
        assert window.isVisible()
        wait_until(lambda: len(ticks) >= 3)
        assert not window.profiles_view.create_button.isEnabled()
        assert io_threads == [io_threads[0]]
        assert io_threads[0] != threading.get_ident()
    finally:
        timer.stop()
        release.set()
    wait_until(lambda: not window.controller.busy)
    assert [player.name for player in players.get_all_players()] == ["Jedna operacja"]
    assert window.controller.session.game.player.name == "Jedna operacja"


def test_missing_profile_preserves_session_and_allows_retry(make_window, wait_until):
    profile = PlayerRepository().add_player("Aktywny")
    window = make_window()
    wait_until(lambda: not window.controller.busy)
    select_existing(window, profile.id, wait_until)
    original = window.controller.session
    window.show_profiles()
    wait_until(lambda: not window.controller.busy)
    assert window.controller.select_profile(-1)
    wait_until(lambda: not window.controller.busy)
    assert window.controller.session is original
    assert "Nie znaleziono" in window.profiles_view.message.text()
    assert window.profiles_view.profile_list.count() == 1
    select_existing(window, profile.id, wait_until)


def test_failed_list_read_can_be_retried_without_rebuilding_view(make_window, wait_until):
    class ReadFailureRepository(PlayerRepository):
        fail = True

        def get_all_players(self):
            if self.fail:
                raise sqlite3.OperationalError("test odczytu")
            return super().get_all_players()

    PlayerRepository().add_player("Odzyskany")
    players = ReadFailureRepository()
    window = make_window(ApplicationController(players=players))
    wait_until(lambda: not window.controller.busy)
    view = window.profiles_view
    assert "odczytać" in view.message.text()
    players.fail = False
    QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    assert window.profiles_view is view
    assert view.profile_list.count() == 1
    assert not view.message.text()
    assert not window.statusBar().currentMessage()


def test_close_while_initial_load_is_pending_then_clean_shutdown(qapp, initialized_db, wait_until):
    window = MainWindow()
    stopped = []
    window.controller.shutdown_finished.connect(lambda: stopped.append(True))
    window.show()
    window.start()
    window.close()
    assert window.isVisible()
    wait_until(lambda: not window.controller.busy)
    window.close()
    wait_until(lambda: stopped and not window.isVisible())
    assert stopped == [True]


def test_plain_text_profile_names_and_future_features_disabled(make_window, wait_until):
    profile = PlayerRepository().add_player("<b>Gracz & profil</b>")
    window = make_window()
    wait_until(lambda: not window.controller.busy)
    select_existing(window, profile.id, wait_until)
    assert window.menu_view.player_label.textFormat() == Qt.TextFormat.PlainText
    assert profile.name in window.menu_view.player_label.text()
    from PySide6.QtWidgets import QPushButton
    future = [button for button in window.menu_view.findChildren(QPushButton)
              if button.text() == "Ustawienia"]
    assert len(future) == 1
    assert all(not button.isEnabled() and button.toolTip() for button in future)
    assert window.menu_view.game_button.isEnabled()
    assert window.menu_view.statistics_button.isEnabled()
    assert window.menu_view.leaderboard_button.isEnabled()
    assert window.menu_view.shop_button.isEnabled()


@pytest.mark.parametrize("state", ["pending", "animating"])
def test_back_to_menu_is_blocked_for_pending_or_animation(make_window, wait_until, monkeypatch, state):
    profile = PlayerRepository().add_player("Powrót")
    window = make_window()
    wait_until(lambda: not window.controller.busy)
    select_existing(window, profile.id, wait_until)
    window.show_profiles()
    wait_until(lambda: not window.controller.busy)
    session = window.controller.session
    if state == "animating":
        window.controller.animating = True
    else:
        session.game.place_bet(Bet(5, BetType.RED))
        with monkeypatch.context() as patch:
            def fail_save(*args, **kwargs):
                raise sqlite3.OperationalError("test pending")
            patch.setattr(RoundRepository, "save_round", fail_save)
            with pytest.raises(sqlite3.OperationalError):
                session.spin_and_save()
    window.show_menu()
    assert window.stack.currentWidget() is window.profiles_view
    assert not window.profiles_view.back_button.isEnabled()
    assert window.statusBar().currentMessage()


def test_return_with_active_bet_preserves_session(make_window, wait_until):
    profile = PlayerRepository().add_player("Aktywny zakład")
    window = make_window()
    wait_until(lambda: not window.controller.busy)
    select_existing(window, profile.id, wait_until)
    window.show_profiles()
    wait_until(lambda: not window.controller.busy)
    session = window.controller.session
    session.game.place_bet(Bet(5, BetType.RED))
    window.show_menu()
    assert window.stack.currentWidget() is window.menu_view
    assert window.controller.session is session
    assert session.game.total_stake == 5


def test_duplicate_error_restores_name_focus(make_window, wait_until, qapp):
    PlayerRepository().add_player("Duplikat")
    window = make_window()
    wait_until(lambda: not window.controller.busy)
    field = window.profiles_view.name_input
    field.setText("Duplikat")
    field.setFocus()
    QTest.keyClick(field, Qt.Key.Key_Return)
    wait_until(lambda: not window.controller.busy)
    assert "już istnieje" in window.profiles_view.message.text()
    assert field.text() == "Duplikat"
    assert qapp.focusWidget() is field


def test_enter_activates_focused_buttons(make_window, wait_until):
    window = make_window()
    wait_until(lambda: not window.controller.busy)
    view = window.profiles_view
    view.name_input.setText("Klawiatura")
    view.create_button.setFocus()
    QTest.keyClick(view.create_button, Qt.Key.Key_Return)
    wait_until(lambda: window.controller.session is not None)
    assert window.stack.currentWidget() is window.menu_view
    QTest.keyClick(window.menu_view.change_button, Qt.Key.Key_Enter)
    wait_until(lambda: not window.controller.busy)
    assert window.stack.currentWidget() is view
    view.back_button.setFocus()
    QTest.keyClick(view.back_button, Qt.Key.Key_Space)
    assert window.stack.currentWidget() is window.menu_view
