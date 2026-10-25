
from domain.player import Player
from domain.bet import Bet, BetType
from domain.wheel import Wheel

from services.bet_resolver import resolve_bet, calculate_payout
from services.bet_validator import validate_bet
from .round_result import BetResult, RoundResult


class Game:
    CHIP_VALUES = (5, 10, 25, 50, 100)
    MAX_CHIPS_PER_FIELD = 5

    def __init__(self):
        self.player = Player()
        self._bets: list[Bet] = []
        self._chip_stacks: dict[tuple[BetType, int | None], list[Bet]] = {}
        self.wheel = Wheel()

    @property
    def current_bets(self) -> tuple[Bet, ...]:
        return tuple(self._bets)

    @property
    def total_stake(self) -> int:
        return sum(bet.amount for bet in self._bets)

    @property
    def chip_stacks(self) -> dict[tuple[BetType, int | None], tuple[Bet, ...]]:
        return {
            key: tuple(stack)
            for key, stack in self._chip_stacks.items()
        }

    def place_bet(self, bet: Bet) -> None:
        self.place_bets([bet])

    def place_bets(self, bets: list[Bet]) -> None:
        if not bets:
            raise ValueError("Bets list cannot be empty")

        for bet in bets:
            validate_bet(bet)

        total_amount = sum(bet.amount for bet in bets)

        self.player.debit(total_amount)
        self._bets.extend(bets)

    def place_chip(
        self,
        bet_type: BetType,
        chip_value: int,
        selection: int | None = None
    ) -> None:
        if type(chip_value) is not int or chip_value not in self.CHIP_VALUES:
            raise ValueError("Invalid chip value")

        key = (bet_type, selection)
        stack = self._chip_stacks.get(key, [])

        if len(stack) >= self.MAX_CHIPS_PER_FIELD:
            raise ValueError("Maximum 5 chips per field")

        bet = Bet(chip_value, bet_type, selection)

        # First accept the bet and debit the player.
        self.place_bet(bet)

        # Only accepted bets are added to the chip stack.
        self._chip_stacks.setdefault(key, []).append(bet)

    def remove_chip(
        self,
        bet_type: BetType,
        selection: int | None = None
    ) -> None:
        key = (bet_type, selection)
        stack = self._chip_stacks.get(key, [])

        if not stack:
            raise ValueError("No chips on this field")

        # Last placed chip is removed first (LIFO).
        last_chip = stack[-1]

        self.remove_bet(last_chip)

    def remove_bet(self, bet: Bet) -> None:
        for index, active_bet in enumerate(self._bets):
            if active_bet is bet:
                key = (active_bet.bet_type, active_bet.selection)
                stack = self._chip_stacks.get(key)

                # Synchronize the chip stack if this bet came from a chip.
                if stack is not None:
                    for chip_index, chip_bet in enumerate(stack):
                        if chip_bet is active_bet:
                            del stack[chip_index]

                            if not stack:
                                del self._chip_stacks[key]
                            break

                del self._bets[index]
                self.player.credit(active_bet.amount)
                return

        raise ValueError("Bet does not exist")

    def spin(self) -> RoundResult:
        if not self._bets:
            raise ValueError("No active bets")

        total_stake = self.total_stake
        spin_result = self.wheel.spin()

        bet_results: list[BetResult] = []
        total_payout = 0

        for bet in self._bets:
            won = resolve_bet(spin_result, bet)
            payout = calculate_payout(bet, won)

            bet_results.append(BetResult(bet, won, payout))
            total_payout += payout

        net_profit = total_payout - total_stake

        if total_payout > 0:
            self.player.credit(total_payout)

        self._bets.clear()
        self._chip_stacks.clear()

        return RoundResult(
            pocket=spin_result,
            bet_results=tuple(bet_results),
            total_stake=total_stake,
            total_payout=total_payout,
            net_profit=net_profit
        )
