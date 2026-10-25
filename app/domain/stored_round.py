from dataclasses import dataclass


@dataclass(frozen=True)
class StoredRound:
    id: int
    player_id: int
    winning_number: int
    total_stake: int
    total_payout: int
    net_profit: int
    played_at: str
