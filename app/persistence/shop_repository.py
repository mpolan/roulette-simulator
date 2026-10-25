from .database import get_connection
from domain.badge import Badge
from domain.purchased_badge import PurchasedBadge

class ShopRepository:

    def get_player_badges(self, player_id: int) -> list[PurchasedBadge]:
        with get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM player_badges
                WHERE player_id = ?""",
                (player_id, )
            )
            badges = cursor.fetchall()

            return [PurchasedBadge(badge['id'], badge['player_id'], badge['badge_id'], badge['price_paid'], badge['purchased_at']) for badge in badges]

    def owns_badge(self, player_id: int, badge_id: str) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("""
                SELECT 1 FROM player_badges
                WHERE player_id = ?
                AND badge_id = ?
                LIMIT 1""",
                (player_id, badge_id)
            )
            return cursor.fetchone() is not None

    def purchase_badge(self, player_id: int, badge: Badge) -> tuple[PurchasedBadge, int]:
        if type(badge.price) is not int or badge.price <= 0:
            raise ValueError("Badge price must be a positive integer")

        with get_connection() as conn:
            # Serialize purchases so balance and ownership checks remain valid.
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.execute("""
                SELECT * FROM players
                WHERE id = ?""",
                (player_id, )
            )
            player = cursor.fetchone()
            if player is None:
                raise LookupError("Player does not exists")
            cursor = conn.execute("""
                SELECT * FROM player_badges
                WHERE player_id = ?
                AND badge_id = ?""",
                (player_id, badge.id)
            )
            owned_badge = cursor.fetchone()
            if owned_badge is not None:
                raise ValueError("Player already owns this badge")

            if player['balance'] < badge.price:
                raise ValueError("You cannot buy this badge")

            new_balance = player['balance'] - badge.price

            balance_cursor = conn.execute("""
                UPDATE players
                SET balance = ?
                WHERE id = ?""",
                (new_balance, player_id)
            )
            if balance_cursor.rowcount != 1:
                raise LookupError("Player balance could not be updated")

            purchase_cursor = conn.execute("""
                INSERT INTO player_badges(player_id, badge_id, price_paid)
                VALUES (?, ?, ?)""",
                (player_id, badge.id, badge.price)
            )
            if purchase_cursor.rowcount != 1 or purchase_cursor.lastrowid is None:
                raise RuntimeError("Badge purchase could not be saved")

            purchase = conn.execute(
                "SELECT * FROM player_badges WHERE id = ?",
                (purchase_cursor.lastrowid,)
            ).fetchone()
            if purchase is None:
                raise LookupError("Badge purchase not found after insertion")

            return PurchasedBadge(
                id=purchase["id"],
                player_id=purchase["player_id"],
                badge_id=purchase["badge_id"],
                price_paid=purchase["price_paid"],
                purchased_at=purchase["purchased_at"],
            ), new_balance
