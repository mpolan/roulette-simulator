from domain.player import Player
from domain.bet import Bet
from domain.wheel import Wheel, Pocket

from services.bet_resolver import resolve_bet, calculate_payout
from services.bet_validator import validate_bet

class Game():
    def __init__(self):
        self.player = Player()
        self.current_bet: Bet | None = None
        self.wheel = Wheel()

    def place_bet(self, bet: Bet):
        if self.current_bet is not None:
            raise ValueError("Bet already placed")
        validate_bet(bet)
        self.player.debit(bet.amount)
        self.current_bet = bet

    def spin(self) -> tuple[Pocket, int]:
        spin_result = self.wheel.spin()
        amount_won = 0
        if self.current_bet is None:
            raise ValueError("No active bet")
        
        if resolve_bet(spin_result, self.current_bet):
            amount_won = calculate_payout(self.current_bet, True)
            self.player.credit(amount_won)

        self.current_bet = None

        return spin_result, amount_won
