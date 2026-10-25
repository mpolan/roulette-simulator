from .database import get_connection
from domain.player_profile import PlayerProfile

class PlayerRepository:
    def get_all_players(self) -> list[PlayerProfile]:  
        with get_connection() as conn:
            cursor = conn.execute("SELECT * FROM players")
            players = cursor.fetchall()

            return [PlayerProfile(player["id"], player["name"], player["balance"]) for player in players]
        
    def get_player(self, player_id: int) -> PlayerProfile | None:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM players WHERE id = ?",
                (player_id, )
            )
            player = cursor.fetchone()
            
            if player is None:
                return None
            
            return PlayerProfile(player["id"], player["name"], player["balance"])
    
    def add_player(self, name: str) -> PlayerProfile:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO players (name) VALUES (?)",
                (name,)
            )

            player_id = cursor.lastrowid

        player = self.get_player(player_id)
        if player is None:
            raise LookupError("Player not found after creation")
        return player

    def update_balance(self, player_id: int, balance: int) -> PlayerProfile:
        if balance < 0:
            raise ValueError("Balance must be greater or equal to 0")
        with get_connection() as conn:
            cursor = conn.execute("""
                UPDATE players
                SET balance = ?
                WHERE id = ?""",
                (balance, player_id)
            )
            if cursor.rowcount == 0:
                raise LookupError("Player with that id does not exists")

        player = self.get_player(player_id)
        if player is None:
            raise LookupError("Player not found after balance update")
        return player

