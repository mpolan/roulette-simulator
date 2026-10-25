from dataclasses import dataclass


@dataclass(frozen=True)
class LeaderboardEntry:
    player_id: int
    player_name: str
    balance: int
    total_rounds: int
    net_profit: int
    win_rate: float
