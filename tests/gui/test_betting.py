"""Zgodność prezentacji stołu z API Game, bez zapisu roboczej bazy."""

from unittest.mock import Mock

import pytest
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtTest import QTest

from domain.bet import Bet, BetType
from domain.game import Game
from domain.player import Player
from gui.application import create_application
from gui.controllers.game_controller import GameController
from gui.views.game import GameView
from gui.widgets.betting_table import BettingTable
from services.game_session import GameSession


@pytest.fixture
def session():
    return GameSession(1, Game(Player("Gracz", 1000)), Mock())


@pytest.fixture
def controller(session):
    result = GameController()
    result.set_session(session)
    return result


@pytest.fixture
def view(qapp, controller):
    create_application([])
    result = GameView(controller)
    result.resize(900, 620)
    result.show()
    result.activateWindow()
    qapp.processEvents()
    yield result
    result.close()
    result.deleteLater()
    qapp.processEvents()


FIELDS = [(BetType.STRAIGHT, number) for number in range(37)] + [
    (kind, None) for kind in (BetType.RED, BetType.BLACK, BetType.EVEN, BetType.ODD, BetType.LOW, BetType.HIGH)
] + [(kind, group) for kind in (BetType.DOZEN, BetType.COLUMN) for group in (1, 2, 3)]


@pytest.mark.parametrize("kind,selection", FIELDS)
def test_every_table_field_places_via_game(controller, kind, selection):
    assert controller.activate_field(kind, selection)
    game = controller.session.game
    assert game.current_bets == (Bet(25, kind, selection),)
    assert game.chip_stacks[(kind, selection)][0] is game.current_bets[0]
    assert game.player.balance == 975


def test_graphic_layout_colors_all_types_and_group_positions(view, session):
    assert set(view.table.fields) == set(FIELDS)
    assert {kind for kind, selection in view.table.fields} == set(BetType)
    for pocket in session.game.wheel.pockets:
        assert view.table.fields[(BetType.STRAIGHT, pocket.number)].color == {
            "red": "#8C2939", "black": "#15212A", "green": "#176641"
        }[pocket.color.value]
    assert view.table.fields[(BetType.STRAIGHT, 3)].pos().y() < view.table.fields[(BetType.STRAIGHT, 1)].pos().y()
    assert view.table.fields[(BetType.COLUMN, 3)].pos().x() > view.table.fields[(BetType.STRAIGHT, 36)].pos().x()


def test_chips_limit_lifo_refunds_and_distinct_fields(controller):
    errors = []
    controller.error.connect(errors.append)
    game = controller.session.game
    for value in game.CHIP_VALUES:
        assert controller.select_chip(value)
        assert controller.activate_field(BetType.STRAIGHT, 0)
    accepted = game.current_bets
    balance = game.player.balance
    assert not controller.activate_field(BetType.STRAIGHT, 0)
    assert game.player.balance == balance
    assert game.current_bets == accepted
    assert "limit" in errors[-1]
    assert controller.activate_field(BetType.STRAIGHT, 1)
    assert controller.activate_field(BetType.STRAIGHT, 0, remove=True)
    assert game.chip_stacks[(BetType.STRAIGHT, 0)][-1].amount == 50
    assert game.player.balance == balance
    assert not controller.activate_field(BetType.RED, remove=True)


@pytest.mark.parametrize("kind,selection", [(kind, 2 if kind in (BetType.DOZEN, BetType.COLUMN) else None)
                                           for kind in BetType if kind != BetType.STRAIGHT])
def test_classic_types_do_not_create_chip_stacks(controller, kind, selection):
    controller.set_mode("CLASSIC")
    controller.set_kind(kind)
    controller.set_group(2)
    controller.set_amount("17")
    assert controller.confirm_classic()
    game = controller.session.game
    assert game.current_bets == (Bet(17, kind, selection),)
    assert game.chip_stacks == {}
    assert game.player.balance == 983


def test_classic_multiselection_full_stake_atomic_rejection_and_clear(controller):
    controller.set_mode("CLASSIC")
    for number in (0, 18, 36):
        controller.activate_field(BetType.STRAIGHT, number)
    game = controller.session.game
    assert game.current_bets == ()
    controller.set_amount("400")
    assert not controller.confirm_classic()
    assert game.current_bets == ()
    assert game.player.balance == 1000
    assert controller.selected_numbers == {0, 18, 36}
    controller.set_amount("30")
    notifications = []
    controller.state_changed.connect(lambda: notifications.append(True))
    assert controller.confirm_classic()
    assert len(notifications) == 1
    assert game.current_bets == tuple(Bet(30, BetType.STRAIGHT, number) for number in (0, 18, 36))
    assert game.player.balance == 910
    assert not controller.selected_numbers


@pytest.mark.parametrize("amount", ["", "abc", "0", "-5", "1.5"])
def test_invalid_classic_stakes_preserve_game(controller, amount):
    controller.set_mode("CLASSIC")
    controller.set_amount(amount)
    assert not controller.confirm_classic()
    assert controller.session.game.current_bets == ()
    assert controller.session.game.player.balance == 1000


def test_identity_removal_classic_chip_mixing_and_no_classic_limit(controller):
    controller.activate_field(BetType.RED)
    chip = controller.session.game.current_bets[0]
    controller.set_mode("CLASSIC")
    controller.set_amount("25")
    for _ in range(6):
        assert controller.confirm_classic()
    game = controller.session.game
    first_classic = game.current_bets[1]
    assert chip == first_classic and chip is not first_classic
    assert not controller.remove_bet(Bet(25, BetType.RED))
    assert controller.remove_bet(first_classic)
    assert game.current_bets[0] is chip
    assert game.chip_stacks[(BetType.RED, None)] == (chip,)
    controller.set_mode("CHIPS")
    assert controller.activate_field(BetType.RED, remove=True)
    assert len(game.current_bets) == 5
    assert game.chip_stacks == {}
    assert game.player.balance == 875


def test_pending_blocks_all_mutations_without_reroll(controller):
    session = controller.session
    repository = Mock()
    repository.save_round.side_effect = OSError("dysk")
    session = GameSession(1, session.game, repository)
    controller.set_session(session)
    controller.activate_field(BetType.RED)
    session.game.wheel.spin = Mock(return_value=session.game.wheel.pockets[0])
    with pytest.raises(OSError):
        session.spin_and_save()
    assert session.has_pending_round
    balance = session.game.player.balance
    assert not controller.activate_field(BetType.RED)
    assert not controller.set_mode("CLASSIC")
    assert not controller.select_chip(100)
    assert not controller.set_kind(BetType.BLACK)
    assert not controller.set_group(3)
    assert not controller.set_amount("100")
    assert not controller.confirm_classic()
    assert not controller.remove_bet(Bet(25, BetType.RED))
    assert session.game.player.balance == balance
    session.game.wheel.spin.assert_called_once()


def test_application_busy_animation_closing_guard_every_intent(session):
    class Locks(QObject):
        busy_changed = Signal(bool)
        locked = False

        def navigation_blocked(self):
            return self.locked

    app = Locks()
    controller = GameController(app)
    controller.set_session(session)
    app.locked = True
    assert controller.betting_locked
    assert not controller.activate_field(BetType.RED)
    assert not controller.set_mode("CLASSIC")
    assert session.game.current_bets == ()
    notifications = []
    controller.state_changed.connect(lambda: notifications.append(True))
    app.busy_changed.emit(True)
    assert len(notifications) == 1


def field_click(view, kind, selection=None, button=Qt.MouseButton.LeftButton):
    field = view.table.fields[(kind, selection)]
    point = view.table.mapFromScene(field.sceneBoundingRect().center())
    QTest.mouseClick(view.table.viewport(), button, pos=point)


def test_mouse_and_keyboard_add_remove_chips_and_chip_selector(view, controller, qapp):
    game = controller.session.game
    QTest.mouseClick(view.chip_picker.buttons[10], Qt.MouseButton.LeftButton)
    assert controller.chip_value == 10
    assert view.chip_picker.buttons[10].isChecked()
    assert sum(button.isChecked() for button in view.chip_picker.buttons.values()) == 1
    QTest.mouseClick(view.chip_picker.buttons[10], Qt.MouseButton.LeftButton)
    assert view.chip_picker.buttons[10].isChecked()
    field_click(view, BetType.STRAIGHT, 0)
    assert game.current_bets == (Bet(10, BetType.STRAIGHT, 0),)
    assert view.table.fields[(BetType.STRAIGHT, 0)].stack == game.chip_stacks[(BetType.STRAIGHT, 0)]
    assert "990" in view.balance_label.text()
    QTest.keyClick(view.table, Qt.Key.Key_Return)
    QTest.keyClick(view.table, Qt.Key.Key_Space)
    assert len(game.current_bets) == 3
    QTest.keyClick(view.table, Qt.Key.Key_Delete)
    field_click(view, BetType.STRAIGHT, 0, Qt.MouseButton.RightButton)
    assert len(game.current_bets) == 1
    QTest.keyClick(view.table, Qt.Key.Key_Right)
    assert view.table.focus_key != (BetType.STRAIGHT, 0)
    QTest.keyClick(view.table, Qt.Key.Key_Return)
    assert len(game.current_bets) == 2


def test_mouse_classic_multi_and_cart_keyboard_identity(view, controller, qapp):
    view.mode_combo.setCurrentIndex(view.mode_combo.findData("CLASSIC"))
    field_click(view, BetType.STRAIGHT, 0)
    field_click(view, BetType.STRAIGHT, 36)
    view.amount_input.setText("20")
    QTest.keyClick(view.amount_input, Qt.Key.Key_Return)
    game = controller.session.game
    assert game.current_bets == (Bet(20, BetType.STRAIGHT, 0), Bet(20, BetType.STRAIGHT, 36))
    assert view.cart.count() == 2
    second_item = view.cart.item(1)
    second_bet = game.current_bets[1]
    view.cart.setCurrentRow(0)
    QTest.keyClick(view.cart, Qt.Key.Key_Delete)
    assert view.cart.item(0) is second_item
    assert game.current_bets[0] is second_bet
    QTest.mouseClick(view.remove_button, Qt.MouseButton.LeftButton)
    assert game.current_bets == ()
    assert view.cart.count() == 0
    assert game.player.balance == 1000


def test_only_changed_scene_fields_and_cart_rows_update(view, controller):
    game = controller.session.game
    original_fields = dict(view.table.fields)
    controller.activate_field(BetType.RED)
    first = game.current_bets[0]
    original_row = view.cart.rows[id(first)]
    assert view.table.update_fields(game) == []
    game.place_chip(BetType.BLACK, 5)
    assert view.table.update_fields(game) == [(BetType.BLACK, None)]
    controller.refresh()
    assert view.table.fields == original_fields
    assert view.cart.rows[id(first)] is original_row
    controller.remove_bet(game.current_bets[-1])
    assert view.cart.rows[id(first)] is original_row


def test_spin_disabled_no_settlement_and_bet_locks_preserve_widgets(view, controller):
    session = controller.session
    session.spin_and_save = Mock()
    session.game.spin = Mock()
    controller.activate_field(BetType.RED)
    QTest.mouseClick(view.spin_button, Qt.MouseButton.LeftButton)
    session.spin_and_save.assert_not_called()
    session.game.spin.assert_not_called()
    assert not view.spin_button.isEnabled()
    assert len(session.game.current_bets) == 1


def test_alt_shortcuts_mode_and_denomination(view, controller, qapp):
    view.table.setFocus()
    qapp.processEvents()
    QTest.keyClick(view.table, Qt.Key.Key_5, Qt.KeyboardModifier.AltModifier)
    assert controller.chip_value == 100
    QTest.keyClick(view.table, Qt.Key.Key_C, Qt.KeyboardModifier.AltModifier)
    assert controller.mode == "CLASSIC"
    assert view.betting_controls.currentIndex() == 1
    controller.set_amount("7")
    QTest.keyClick(view.table, Qt.Key.Key_Return, Qt.KeyboardModifier.ControlModifier)
    assert controller.session.game.current_bets == (Bet(7, BetType.RED),)


def test_field_stack_references_follow_new_session_with_equal_bets(view, controller):
    controller.activate_field(BetType.RED)
    previous = controller.session.game.current_bets[0]
    game = Game(Player("Drugi", 1000))
    game.place_chip(BetType.RED, 25)
    controller.set_session(GameSession(2, game, Mock()))
    field = view.table.fields[(BetType.RED, None)]
    assert field.stack[0] is game.current_bets[0]
    assert field.stack[0] is not previous


@pytest.mark.parametrize("size", [(740, 530), (900, 620), (1280, 770)])
def test_scene_fits_viewport_at_window_sizes(view, qapp, size):
    view.resize(*size)
    qapp.processEvents()
    assert view.width() <= size[0]
    assert view.height() <= size[1]
    scene_rect = view.table.mapFromScene(view.table.sceneRect()).boundingRect()
    viewport = view.table.viewport().rect()
    assert scene_rect.width() <= viewport.width() + 2
    assert scene_rect.height() <= viewport.height() + 2
    assert view.cart.width() >= 200
    assert view.chip_picker.width() >= 284
    for button in view.chip_picker.buttons.values():
        assert button.height() == 52
        assert button.width() == 52
        assert view.chip_picker.rect().contains(button.geometry())
