from dataclasses import dataclass

from .badge import Badge


@dataclass(frozen=True)
class LeaderboardEntry:
    player_id: int
    player_name: str
    balance: int
    total_rounds: int
    net_profit: int
    win_rate: float
    badges: tuple[Badge, ...] = ()

    @property
    def badge_count(self) -> int:
        return len(self.badges)
