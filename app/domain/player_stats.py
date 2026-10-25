from dataclasses import dataclass

@dataclass(frozen=True)
class PlayerStats:
    player_id: int
    total_rounds: int
    profitable_rounds: int
    total_bets: int
    winning_bets: int
    total_stake: int
    total_payout: int
    net_profit: int
    biggest_payout: int
    win_rate: float
    bet_win_rate: float
