"""Najważniejsze przypadki rankingu na tymczasowej bazie."""

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QTest

from domain.bet import Bet, BetType
from gui.application import create_application
from gui.main_window import MainWindow
from persistence.player_repository import PlayerRepository
from persistence.shop_repository import ShopRepository
from services.leaderboard_service import LeaderboardService
from services.session_factory import create_game_session
from services.shop_service import ShopService


@pytest.fixture
def window(qapp, initialized_db, wait_until):
    create_application([])
    player = PlayerRepository().add_player("Aktywny", 10000)
    window = MainWindow()
    window.show()
    window.controller.select_profile(player.id)
    wait_until(lambda: window.controller.session is not None)
    yield window
    wait_until(lambda: not window.controller.busy)
    window.close()
    wait_until(lambda: not window.isVisible())
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def open_ranking(window, wait_until):
    QTest.mouseClick(window.menu_view.leaderboard_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    assert window.stack.currentWidget() is window.leaderboard
    return window.leaderboard


def choose(view, field, window, wait_until):
    view.sort_combo.setCurrentIndex(view.sort_combo.findData(field))
    wait_until(lambda: not window.controller.busy)


def test_empty_ranking_and_keyboard_navigation(window, wait_until):
    view = open_ranking(window, wait_until)
    assert view.table.rowCount() == 0
    assert "Brak wyników" in view.message.text()
    assert "pierwszą rundę" in view.position_label.text()
    choose(view, "win_rate", window, wait_until)
    assert "10 rund" in view.position_label.text()
    assert "co najmniej 10 rundami" in view.message.text()
    choose(view, "badge_count", window, wait_until)
    assert "Brak zakupionych odznak" in view.message.text()
    QTest.keyClick(view.sort_combo, Qt.Key.Key_Escape)
    assert window.stack.currentWidget() is window.menu_view


def test_real_service_sorting_active_player_and_badges(window, wait_until, monkeypatch):
    active = window.controller.session
    rival = create_game_session(PlayerRepository().add_player("Ryw al", 10000).id)
    for session, count in ((active, 1), (rival, 10)):
        pocket = next(p for p in session.game.wheel.pockets if p.number == 32)
        monkeypatch.setattr(session.game.wheel, "spin", lambda pocket=pocket: pocket)
        for _ in range(count):
            session.game.place_bet(Bet(10, BetType.RED))
            session.spin_and_save()
    ShopService(ShopRepository()).buy_badge(active, "bronze_roller")
    view = open_ranking(window, wait_until)
    assert view.table.rowCount() == 2
    assert view.table.item(0, 1).text() == "Ryw al"
    assert view.table.item(1, 1).text() == "☻ Aktywny (Ty)"
    assert "Bronze Roller" in view.table.item(1, 1).toolTip()
    assert view.table.item(1, 2).text() == "+10$"
    assert view.table.item(1, 5).text() == "1"
    assert view.table.item(1, 6).text() == "7510$"
    assert view.position_label.text() == "Twoja pozycja: #2 / 2"
    first_cell = view.table.item(0, 0)
    QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    assert view.table.item(0, 0) is first_cell
    choose(view, "total_rounds", window, wait_until)
    assert view.table.item(0, 3).text() == "10"
    choose(view, "win_rate", window, wait_until)
    assert view.table.rowCount() == 1
    assert view.table.item(0, 1).text() == "Ryw al"
    assert "10 rund" in view.position_label.text()
    choose(view, "badge_count", window, wait_until)
    assert view.table.rowCount() == 1
    assert view.table.item(0, 1).text() == "☻ Aktywny (Ty)"
    assert view.position_label.text() == "Twoja pozycja: #1 / 1"


def test_read_error_retry_and_changed_sort_clears_old_rows(window, wait_until, monkeypatch):
    session = window.controller.session
    pocket = next(p for p in session.game.wheel.pockets if p.number == 32)
    monkeypatch.setattr(session.game.wheel, "spin", lambda: pocket)
    session.game.place_bet(Bet(10, BetType.RED))
    session.spin_and_save()
    view = open_ranking(window, wait_until)
    assert view.table.rowCount() == 1
    with monkeypatch.context() as patch:
        def fail(*args):
            raise OSError("testowy błąd odczytu")
        patch.setattr(LeaderboardService, "get_leaderboard", fail)
        QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
        wait_until(lambda: not window.controller.busy)
        assert "Nie można odczytać rankingu" in view.message.text()
        assert view.table.rowCount() == 1
        choose(view, "win_rate", window, wait_until)
        assert view.table.rowCount() == 0
        assert "Nie można odczytać rankingu" in view.message.text()
    QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
    wait_until(lambda: not window.controller.busy)
    assert "Brak graczy" in view.message.text()
    assert view.table.rowCount() == 0
