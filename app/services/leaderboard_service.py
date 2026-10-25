from domain.leaderboard_entry import LeaderboardEntry
from persistence.player_repository import PlayerRepository
from services.stats_service import StatsService
from services.shop_service import ShopService


class LeaderboardService:
    MIN_ROUNDS_FOR_WIN_RATE = 10
    SORT_FIELDS = ("net_profit", "total_rounds", "win_rate", "badge_count")

    def __init__(self, player_repository: PlayerRepository, stats_service: StatsService, shop_service: ShopService) -> None:
        self._player_repository = player_repository
        self._stats_service = stats_service
        self._shop_service = shop_service

    def get_leaderboard(self, sort_by: str = "net_profit") -> list[LeaderboardEntry]:
        if sort_by not in self.SORT_FIELDS:
            raise ValueError(f"Unsupported leaderboard sort: {sort_by!r}")

        entries = []
        for player in self._player_repository.get_all_players():
            stats = self._stats_service.get_player_stats(player.id)
            badges = tuple(self._shop_service.get_owned_badges(player.id))
            if sort_by == "badge_count":
                if not badges:
                    continue
            elif stats.total_rounds == 0:
                continue
            if sort_by == "win_rate" and stats.total_rounds < self.MIN_ROUNDS_FOR_WIN_RATE:
                continue
            entries.append(LeaderboardEntry(
                player_id=player.id,
                player_name=player.name,
                balance=player.balance,
                total_rounds=stats.total_rounds,
                net_profit=stats.net_profit,
                win_rate=stats.win_rate,
                badges=badges,
            ))

        return sorted(entries, key=lambda entry: (-getattr(entry, sort_by), entry.player_id))
