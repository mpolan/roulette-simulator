from textual.app import App

from persistence.player_repository import PlayerRepository
from persistence.round_repository import RoundRepository
from screens.game import GameScreen
from screens.navigation import MainMenu, ProfileScreen
from screens.statistics import StatisticsScreen
from services.game_session import GameSession
from services.session_factory import create_game_session
from services.stats_service import StatsService


class RouletteApp(App):
    CSS_PATH = "ui.tcss"

    def __init__(self) -> None:
        super().__init__(ansi_color=False)
        self.players = PlayerRepository()
        self.stats = StatsService(RoundRepository())
        self.session: GameSession | None = None
        self.player_id: int | None = None

    def on_mount(self) -> None:
        self.title = "ROULETTE SIMULATOR"
        self.sub_title = "Obsidian Royale"
        self.push_screen(ProfileScreen())

    def choose_player(self, player_id: int) -> None:
        if self.session is not None and (
            self.session.has_pending_round or self.session.game.current_bets
        ):
            raise ValueError("Najpierw rozlicz lub usuń aktywne zakłady i zapisz rundę.")
        session = create_game_session(player_id)
        self.session = session
        self.player_id = player_id
        self.switch_screen(MainMenu())

    def play(self) -> None:
        if self.session is not None:
            self.push_screen(GameScreen(self.session))

    def change_profile(self) -> None:
        if self.session is not None:
            if self.session.has_pending_round or self.session.game.current_bets:
                self.notify("Najpierw rozlicz lub usuń aktywne zakłady i zapisz rundę.", severity="warning")
                return
        self.switch_screen(ProfileScreen())

    def show_statistics(self) -> None:
        if self.player_id is not None:
            self.push_screen(StatisticsScreen(self.player_id))

    def action_quit(self) -> None:
        if self.session is not None and (
            self.session.has_pending_round or self.session.game.current_bets
        ):
            self.notify("Przed wyjściem usuń lub rozlicz zakłady i zapisz rundę.", severity="warning")
            return
        if isinstance(self.screen, GameScreen) and self.screen.animating:
            return
        self.exit()
