from dataclasses import dataclass

from .bet import Bet
from .wheel import Pocket

@dataclass(frozen=True)
class BetResult:
    bet: Bet
    won: bool
    payout: int


@dataclass(frozen=True)
class RoundResult:
    pocket: Pocket
    bet_results: tuple[BetResult, ...]
    total_stake: int
    total_payout: int
    net_profit: int
