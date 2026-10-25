from .game_session import GameSession
from domain.player import Player
from domain.game import Game
from persistence.player_repository import PlayerRepository
from persistence.round_repository import RoundRepository

def create_game_session(player_id: int) -> GameSession:
    player_repository = PlayerRepository()
    player = player_repository.get_player(player_id)
    if not player:
        raise LookupError("Player does not exists")

    player_obj = Player(player.name, player.balance)
    game_obj = Game(player_obj)

    round_repository_obj = RoundRepository()
    game_session_obj = GameSession(player_id, game_obj, round_repository_obj)

    return game_session_obj
