from domain.badge import Badge

class BadgeCatalog:
    def __init__(self) -> None:
        self._badges: dict[str, Badge] = {
            badge.id: badge for badge in (
                Badge("bronze_roller", "Bronze Roller", 2500, "🥉", "Brązowa odznaka gracza stawiającego pierwsze kroki przy stole."),
                Badge("silver_roller", "Silver Roller", 5000, "🥈", "Srebrna odznaka stałego bywalca stołu ruletki."),
                Badge("golden_roller", "Golden Roller", 10000, "🥇", "Złota odznaka dla gracza, który lubi wyróżniać się przy stole."),
                Badge("diamond_roller", "Diamond Roller", 25000, "💎", "Diamentowa odznaka dla kolekcjonera prestiżowych oznaczeń."),
                Badge("casino_roller", "Casino Roller", 50000, "👑", "Najdroższa odznaka w kolekcji Obsidian Royale."),
            )
        }

    def get_all_badges(self) -> tuple[Badge, ...]:
        return tuple(self._badges.values())

    def get_badge(self, badge_id: str) -> Badge | None:
        return self._badges.get(badge_id)
