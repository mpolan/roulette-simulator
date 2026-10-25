from services.game_session import GameSession
from persistence.shop_repository import ShopRepository
from domain.badge import Badge
from domain.purchased_badge import PurchasedBadge
from services.badge_catalog import BadgeCatalog


class ShopService:
    def __init__(
        self,
        shop_repository: ShopRepository,
        badge_catalog: BadgeCatalog | None = None,
    ) -> None:
        self._shop_repository = shop_repository
        self._badge_catalog = badge_catalog if badge_catalog is not None else BadgeCatalog()

    def get_catalog(self) -> tuple[Badge, ...]:
        return self._badge_catalog.get_all_badges()

    def get_owned_badges(self, player_id: int) -> list[Badge]:
        purchases = self._shop_repository.get_player_badges(player_id)
        badges = []
        for purchase in purchases:
            badge = self._badge_catalog.get_badge(purchase.badge_id)
            if badge is not None:
                badges.append(badge)
        return badges

    def get_total_spent(self, player_id: int) -> int:
        purchases = self._shop_repository.get_player_badges(player_id)
        return sum(purchase.price_paid for purchase in purchases)

    def buy_badge(self, session: GameSession, badge_id: str) -> PurchasedBadge:
        badge = self._badge_catalog.get_badge(badge_id)
        if badge is None:
            raise ValueError("Badge does not exist")
        if session.has_pending_round or session.game.current_bets:
            raise RuntimeError("Resolve active bets and save the pending round before buying a badge")

        purchase, new_balance = self._shop_repository.purchase_badge(session.player_id, badge)
        session.game.player.balance = new_balance
        return purchase
