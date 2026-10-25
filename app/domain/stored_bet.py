from dataclasses import dataclass

from .bet import BetType


@dataclass(frozen=True)
class StoredBet:
    id: int
    round_id: int
    bet_type: BetType
    selection: int | None
    amount: int
    won: bool
    payout: int
