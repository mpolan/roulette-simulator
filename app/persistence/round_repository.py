from domain.bet import BetType
from domain.round_result import RoundResult
from domain.stored_bet import StoredBet
from domain.stored_round import StoredRound
from .database import get_connection

class RoundRepository:
    def save_round(self, player_id: int, result: RoundResult) -> int:
        with get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO rounds (player_id, winning_number, total_stake, total_payout, net_profit) 
                VALUES (?, ?, ?, ?, ?)""",
                (player_id, result.pocket.number, result.total_stake, result.total_payout, result.net_profit)
            )
            round_id = cursor.lastrowid

            for bet_result in result.bet_results:
                conn.execute("""
                    INSERT INTO round_bets (round_id, bet_type, selection, amount, won, payout)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (round_id, bet_result.bet.bet_type.value, bet_result.bet.selection,
                     bet_result.bet.amount, bet_result.won, bet_result.payout)
                )

            return round_id

    def get_player_rounds(self, player_id: int) -> list[StoredRound]:
        with get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM rounds WHERE player_id = ?
                ORDER BY id DESC""",
                (player_id, )
            )
            rounds = cursor.fetchall()
            return [StoredRound(
                id=row["id"],
                player_id=row["player_id"],
                winning_number=row["winning_number"],
                total_stake=row["total_stake"],
                total_payout=row["total_payout"],
                net_profit=row["net_profit"],
                played_at=row["played_at"],
            ) for row in rounds]

    def get_player_bets(self, player_id: int) -> list[StoredBet]:
        with get_connection() as conn:
            cursor = conn.execute("""
                SELECT round_bets.id, round_bets.round_id,
                       bet_type, selection, amount, won, payout
                FROM round_bets 
                JOIN rounds 
                ON rounds.id = round_bets.round_id
                WHERE rounds.player_id = ?
                ORDER BY rounds.id DESC, round_bets.id ASC""",
                (player_id, )
            )
            bets = cursor.fetchall()
            return [StoredBet(
                id=row["id"],
                round_id=row["round_id"],
                bet_type=BetType(row["bet_type"]),
                selection=row["selection"],
                amount=row["amount"],
                won=bool(row["won"]),
                payout=row["payout"],
            ) for row in bets]
