"""Regresje publicznego API silnika, niezależne od prezentacji."""

import pytest

from domain.bet import Bet, BetType
from domain.game import Game
from domain.player import Player
from domain.wheel import PocketColor, Wheel


RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
OUTSIDE_CASES = [
    (BetType.RED, None, RED_NUMBERS, 2),
    (BetType.BLACK, None, set(range(1, 37)) - RED_NUMBERS, 2),
    (BetType.EVEN, None, set(range(2, 37, 2)), 2),
    (BetType.ODD, None, set(range(1, 37, 2)), 2),
    (BetType.LOW, None, set(range(1, 19)), 2),
    (BetType.HIGH, None, set(range(19, 37)), 2),
    (BetType.DOZEN, 1, set(range(1, 13)), 3),
    (BetType.DOZEN, 2, set(range(13, 25)), 3),
    (BetType.DOZEN, 3, set(range(25, 37)), 3),
    (BetType.COLUMN, 1, set(range(1, 37, 3)), 3),
    (BetType.COLUMN, 2, set(range(2, 37, 3)), 3),
    (BetType.COLUMN, 3, set(range(3, 37, 3)), 3),
]


def fixed_pocket(game, monkeypatch, number):
    pocket = next(p for p in game.wheel.pockets if p.number == number)
    monkeypatch.setattr(game.wheel, "spin", lambda: pocket)
    return pocket


def test_european_wheel_order_and_colors():
    pockets = Wheel().pockets
    assert isinstance(pockets, tuple)
    assert [p.number for p in pockets] == [
        0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8,
        23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26,
    ]
    assert {p.number for p in pockets if p.color is PocketColor.RED} == RED_NUMBERS
    assert sum(p.color is PocketColor.BLACK for p in pockets) == 18
    assert [p.number for p in pockets if p.color is PocketColor.GREEN] == [0]


@pytest.mark.parametrize("kind,selection,winning_numbers,multiplier", OUTSIDE_CASES)
@pytest.mark.parametrize("number", range(37))
def test_outside_settlement_for_every_pocket(monkeypatch, kind, selection, winning_numbers, multiplier, number):
    game = Game(Player(balance=1000))
    pocket = fixed_pocket(game, monkeypatch, number)
    bet = Bet(10, kind, selection)
    game.place_bet(bet)
    result = game.spin()
    won = number in winning_numbers
    payout = 10 * multiplier if won else 0
    assert result.pocket is pocket
    assert result.total_stake == 10
    assert result.total_payout == payout
    assert result.net_profit == payout - 10
    assert result.bet_results[0].bet is bet
    assert result.bet_results[0].won is won
    assert result.bet_results[0].payout == payout
    assert game.player.balance == 990 + payout
    assert game.current_bets == ()
    assert game.chip_stacks == {}


@pytest.mark.parametrize("selection", range(37))
@pytest.mark.parametrize("won", [False, True])
def test_straight_wins_and_losses_including_zero(monkeypatch, selection, won):
    game = Game(Player(balance=1000))
    number = selection if won else (selection + 1) % 37
    fixed_pocket(game, monkeypatch, number)
    game.place_chip(BetType.STRAIGHT, 5, selection)
    result = game.spin()
    assert result.total_payout == (180 if won else 0)
    assert result.net_profit == (175 if won else -5)
    assert game.player.balance == (1175 if won else 995)
    assert game.current_bets == ()
    assert game.chip_stacks == {}


@pytest.mark.parametrize("bad_bet", [
    Bet(0, BetType.RED), Bet(-1, BetType.RED), Bet(True, BetType.RED),
    Bet(1.5, BetType.RED), Bet("10", BetType.RED), Bet(5, "red"),
    Bet(5, BetType.STRAIGHT), Bet(5, BetType.STRAIGHT, -1),
    Bet(5, BetType.STRAIGHT, 37), Bet(5, BetType.STRAIGHT, True),
    Bet(5, BetType.DOZEN, 0), Bet(5, BetType.COLUMN, 4),
    Bet(5, BetType.DOZEN, 1.0), Bet(5, BetType.RED, 1),
])
def test_invalid_batch_preserves_existing_state(bad_bet):
    game = Game(Player(balance=1000))
    game.place_chip(BetType.BLACK, 25)
    before_bets, before_stacks = game.current_bets, game.chip_stacks
    with pytest.raises(ValueError):
        game.place_bets([Bet(10, BetType.RED), bad_bet])
    assert game.player.balance == 975
    assert game.current_bets == before_bets
    assert game.chip_stacks == before_stacks


def test_empty_batch_and_insufficient_funds_are_atomic():
    game = Game(Player(balance=20))
    for bets in ([], [Bet(10, BetType.RED), Bet(15, BetType.BLACK)]):
        with pytest.raises(ValueError):
            game.place_bets(bets)
        assert game.player.balance == 20
        assert game.current_bets == ()
    with pytest.raises(ValueError):
        game.spin()


def test_duplicate_bets_are_removed_by_identity_and_refunded_once():
    game = Game(Player(balance=100))
    first, second = Bet(10, BetType.RED), Bet(10, BetType.RED)
    game.place_bets([first, second])
    with pytest.raises(ValueError):
        game.remove_bet(Bet(10, BetType.RED))
    game.remove_bet(second)
    assert len(game.current_bets) == 1
    assert game.current_bets[0] is first
    assert game.player.balance == 90
    with pytest.raises(ValueError):
        game.remove_bet(second)
    assert game.player.balance == 90


@pytest.mark.parametrize("value", [5, 10, 25, 50, 100])
def test_supported_chips_and_lifo(value):
    game = Game(Player(balance=1000))
    game.place_chip(BetType.STRAIGHT, value, 0)
    game.place_chip(BetType.STRAIGHT, 25, 0)
    first, last = game.current_bets
    game.remove_chip(BetType.STRAIGHT, 0)
    assert game.current_bets[0] is first
    assert all(bet is not last for bet in game.current_bets)
    assert game.chip_stacks[(BetType.STRAIGHT, 0)] == (first,)
    assert game.player.balance == 1000 - value
    game.remove_bet(first)
    assert game.chip_stacks == {}
    assert game.player.balance == 1000


@pytest.mark.parametrize("value", [1, 20, True, 5.0, "5"])
def test_invalid_chip_does_not_change_state(value):
    game = Game(Player(balance=1000))
    with pytest.raises(ValueError):
        game.place_chip(BetType.RED, value)
    assert game.player.balance == 1000
    assert game.current_bets == ()
    assert game.chip_stacks == {}


def test_chip_limit_is_per_field_and_does_not_limit_classic_bets():
    game = Game(Player(balance=1000))
    for _ in range(5):
        game.place_chip(BetType.RED, 5)
    with pytest.raises(ValueError):
        game.place_chip(BetType.RED, 5)
    assert game.player.balance == 975
    game.place_chip(BetType.BLACK, 5)
    classic = Bet(10, BetType.RED)
    game.place_bet(classic)
    assert len(game.chip_stacks[(BetType.RED, None)]) == 5
    assert len(game.current_bets) == 7
    game.remove_bet(classic)
    assert len(game.chip_stacks[(BetType.RED, None)]) == 5
    assert game.player.balance == 970


def test_failed_chip_placement_and_empty_removal_leave_no_stack():
    game = Game(Player(balance=0))
    with pytest.raises(ValueError):
        game.place_chip(BetType.RED, 5)
    with pytest.raises(ValueError):
        game.remove_chip(BetType.RED)
    assert game.current_bets == ()
    assert game.chip_stacks == {}
    assert game.player.balance == 0


def test_multiple_straights_charge_full_amount_per_number_and_settle_once(monkeypatch):
    game = Game(Player(balance=1000))
    fixed_pocket(game, monkeypatch, 1)
    bets = [Bet(10, BetType.STRAIGHT, 1), Bet(10, BetType.STRAIGHT, 2)]
    game.place_bets(bets)
    assert game.total_stake == 20
    assert game.player.balance == 980
    result = game.spin()
    assert result.total_stake == 20
    assert result.total_payout == 360
    assert result.net_profit == 340
    assert game.player.balance == 1340
    assert len(result.bet_results) == 2
