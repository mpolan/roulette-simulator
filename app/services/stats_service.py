from persistence.round_repository import RoundRepository
from domain.player_stats import PlayerStats

class StatsService:
    def __init__(self, round_repository: RoundRepository) -> None:
        self._round_repository = round_repository

    def get_player_stats(self, player_id: int) -> PlayerStats:
        rounds = self._round_repository.get_player_rounds(player_id)
        bets = self._round_repository.get_player_bets(player_id)

        profitable_rounds = sum(1 for round in rounds if round.net_profit > 0)
        winning_bets = sum(1 for bet in bets if bet.won)
        total_rounds = len(rounds)
        total_bets = len(bets)

        return PlayerStats(
            player_id=player_id,
            total_rounds=total_rounds,
            profitable_rounds=profitable_rounds,
            total_bets=total_bets,
            winning_bets=winning_bets,
            total_stake=sum(round.total_stake for round in rounds),
            total_payout=sum(round.total_payout for round in rounds),
            net_profit=sum(round.net_profit for round in rounds),
            biggest_payout=max((round.total_payout for round in rounds), default=0),
            win_rate=profitable_rounds / total_rounds * 100 if total_rounds else 0.0,
            bet_win_rate=winning_bets / total_bets * 100 if total_bets else 0.0,
        )
