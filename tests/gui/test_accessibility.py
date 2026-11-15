"""Celowane regresje rozmiaru okna i obsługi klawiaturą z Etapu 8."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QTest

from domain.badge import Badge
from domain.bet import BetType
from domain.game import Game
from domain.leaderboard_entry import LeaderboardEntry
from domain.player import Player
from gui.application import create_application
from gui.controllers.game_controller import GameController
from gui.views.game import GameView
from gui.views.leaderboard import LeaderboardView
from gui.views.profiles import ProfilesView
from services.game_session import GameSession


@pytest.fixture
def show_widget(qapp):
    create_application([])
    widgets = []

    def show(widget, width=740, height=536):
        widgets.append(widget)
        widget.resize(width, height)
        widget.show()
        widget.activateWindow()
        qapp.processEvents()
        return widget

    yield show
    for widget in widgets:
        widget.close()
        widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_small_profiles_keep_rows_and_actions_visible(show_widget, qapp):
    view = ProfilesView()
    long_name = "Profil demonstracyjny o bardzo długiej nazwie"
    view.set_profiles([SimpleNamespace(id=i, name=long_name, balance=10000) for i in range(8)])
    show_widget(view)
    assert (view.width(), view.height()) == (740, 536)
    assert view.profile_list.viewport().height() >= 3 * view.profile_list.sizeHintForRow(0)
    assert view.profile_list.geometry().bottom() < view.select_button.geometry().top()
    assert not view.profile_list.horizontalScrollBar().isVisible()
    assert long_name in view.profile_list.item(0).toolTip()
    assert "10000$" in view.profile_list.item(0).toolTip()
    for widget in (view.name_input, view.create_button, view.select_button, view.exit_button):
        top_left = widget.mapTo(view, widget.rect().topLeft())
        bottom_right = widget.mapTo(view, widget.rect().bottomRight())
        assert view.rect().contains(top_left) and view.rect().contains(bottom_right)
    view.profile_list.setFocus()
    QTest.keyClick(view.profile_list, Qt.Key.Key_Down)
    assert view.profile_list.currentRow() == 1


def game_view(show_widget):
    controller = GameController()
    controller.set_session(GameSession(1, Game(Player("Klawiatura", 1000)), Mock()))
    return show_widget(GameView(controller)), controller


def test_remove_action_keeps_keyboard_focus_during_refresh(show_widget, qapp):
    view, controller = game_view(show_widget)
    controller.activate_field(BetType.RED)
    controller.activate_field(BetType.BLACK)
    view.remove_button.setFocus()
    controller.refresh()
    assert qapp.focusWidget() is view.remove_button
    QTest.keyClick(view.remove_button, Qt.Key.Key_Return)
    assert len(controller.session.game.current_bets) == 1
    assert qapp.focusWidget() is view.remove_button


def test_chip_focus_and_keyboard_activation_preserve_selection(show_widget, qapp):
    view, controller = game_view(show_widget)
    first = view.chip_picker.buttons[5]
    second = view.chip_picker.buttons[10]
    first.setFocus()
    QTest.keyClick(first, Qt.Key.Key_Space)
    assert controller.chip_value == 5 and first.isChecked()
    second.setFocus()
    assert qapp.focusWidget() is second and first.isChecked()
    QTest.keyClick(second, Qt.Key.Key_Return)
    assert controller.chip_value == 10 and second.isChecked()
    assert not first.isChecked()


def test_ranking_tooltip_exposes_full_name_and_badges(show_widget):
    view = show_widget(LeaderboardView())
    name = "Profil o długiej nazwie widocznej w podpowiedzi"
    badge = Badge("test", "Odznaka demonstracyjna", 2500, "☻", "Opis")
    view.set_data([LeaderboardEntry(1, name, 1000, 10, 100, 50., (badge,))], 1)
    tooltip = view.table.item(0, 1).toolTip()
    assert name in tooltip
    assert "☻ Odznaka demonstracyjna" in tooltip
