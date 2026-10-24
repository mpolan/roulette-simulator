
from domain.player import Player
from domain.bet import Bet
from domain.wheel import Wheel, Pocket

from services.bet_resolver import resolve_bet, calculate_payout
from services.bet_validator import validate_bet
from .round_result import BetResult, RoundResult

class Game:
    def __init__(self):
        self.player = Player()
        self._bets: list[Bet] = []
        self.wheel = Wheel()

    @property
    def current_bets(self) -> tuple[Bet, ...]:
        return tuple(self._bets)

    @property
    def total_stake(self) -> int:
        return sum(bet.amount for bet in self._bets)

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

    def remove_bet(self, bet: Bet) -> None:
        if bet not in self._bets:
            raise ValueError("Bet does not exist")

        self._bets.remove(bet)
        self.player.credit(bet.amount)

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

        return RoundResult(spin_result, tuple(bet_results), total_stake, total_payout, net_profit)
