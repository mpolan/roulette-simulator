from .database import get_connection
from domain.player_profile import PlayerProfile

class PlayerRepository:
    def get_all_players(self) -> list[PlayerProfile]:  
        with get_connection() as conn:
            cursor = conn.execute("SELECT * FROM players")
            players = cursor.fetchall()

            return [PlayerProfile(player["id"], player["name"]) for player in players]
        
    def get_player(self, uid: int) -> PlayerProfile | None:  
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM players WHERE id = ?",
                (uid, )
            )
            player = cursor.fetchone()
            
            if player is None:
                return None
            
            return PlayerProfile(player["id"], player["name"])
    
    def add_player(self, name: str) -> PlayerProfile:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO players (name) VALUES (?)",
                (name,)
            )

            player_id = cursor.lastrowid
            return PlayerProfile(player_id, name)

