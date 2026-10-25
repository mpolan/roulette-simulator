
from domain.game import Game
from domain.round_result import RoundResult
from persistence.round_repository import RoundRepository


class GameSession:
    def __init__(self, player_id: int, game: Game, round_repository: RoundRepository) -> None:
        self._player_id = player_id
        self._game = game
        self._round_repository = round_repository

        self._pending_result: RoundResult | None = None
        self._pending_balance: int | None = None

    @property
    def player_id(self) -> int:
        return self._player_id

    @property
    def game(self) -> Game:
        return self._game

    @property
    def has_pending_round(self) -> bool:
        return self._pending_result is not None

    def spin_and_save(self) -> RoundResult:
        if self._pending_result is not None:
            raise RuntimeError("Previous round has not been saved")

        result = self._game.spin()

        self._pending_result = result
        self._pending_balance = self._game.player.balance

        return self.save_pending_round()

    def save_pending_round(self) -> RoundResult:
        if self._pending_result is None or self._pending_balance is None:
            raise RuntimeError("No pending round to save")

        result = self._pending_result

        self._round_repository.save_round(
            player_id=self._player_id,
            result=result,
            balance_after=self._pending_balance
        )

        self._pending_result = None
        self._pending_balance = None

        return result
