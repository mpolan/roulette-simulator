from dataclasses import dataclass

@dataclass(frozen=True)
class PurchasedBadge:
    id: int
    player_id: int
    badge_id: str
    price_paid: int
    purchased_at: str
