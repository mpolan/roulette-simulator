import sqlite3

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Select, Static


class ProfileScreen(Screen):
    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="navigation-panel"):
            yield Static("OBSIDIAN ROYALE", classes="panel-title")
            yield Static("WYBIERZ GRACZA", classes="panel-subtitle")
            yield Select([], prompt="Wybierz profil", id="profile-select")
            yield Button("Wybierz profil", id="profile-open", disabled=True)
            yield Static("NOWY PROFIL", classes="section-title")
            yield Input(placeholder="Nazwa gracza", max_length=40, id="profile-name")
            yield Button("Utwórz profil", id="profile-create")
            yield Static("", id="profile-message", classes="error-message", markup=False)
            yield Button("Powrót do menu", id="profile-back", disabled=self.app.session is None)
            yield Button("Wyjdź", id="profile-exit")

    def on_mount(self) -> None:
        self.load_profiles()

    def load_profiles(self) -> None:
        try:
            profiles = self.app.players.get_all_players()
        except sqlite3.Error as error:
            self.query_one("#profile-message", Static).update(f"Nie można odczytać profili: {error}")
            return
        self.query_one("#profile-select", Select).set_options(
            (f"{profile.name} — {profile.balance}$", profile.id) for profile in profiles
        )
        if not profiles:
            self.query_one("#profile-message", Static).update("Brak profili. Utwórz pierwszego gracza.")
            self.query_one("#profile-name", Input).focus()

    @on(Select.Changed, "#profile-select")
    def selection_changed(self, event: Select.Changed) -> None:
        self.query_one("#profile-open", Button).disabled = event.value is Select.BLANK

    def open_profile(self, player_id: int) -> None:
        try:
            self.app.choose_player(player_id)
        except (sqlite3.Error, LookupError, ValueError) as error:
            self.query_one("#profile-message", Static).update(f"Nie można otworzyć profilu: {error}")

    @on(Button.Pressed, "#profile-open")
    def choose(self) -> None:
        value = self.query_one("#profile-select", Select).value
        if value is not Select.BLANK:
            self.open_profile(value)

    @on(Input.Submitted, "#profile-name")
    @on(Button.Pressed, "#profile-create")
    def create(self) -> None:
        name = self.query_one("#profile-name", Input).value.strip()
        message = self.query_one("#profile-message", Static)
        if not name:
            message.update("Podaj nazwę gracza.")
            return
        try:
            profile = self.app.players.add_player(name)
        except sqlite3.IntegrityError:
            message.update("Profil o tej nazwie już istnieje. Wybierz inną nazwę.")
            return
        except (sqlite3.Error, LookupError) as error:
            message.update(f"Nie można utworzyć profilu: {error}")
            return
        self.open_profile(profile.id)

    @on(Button.Pressed, "#profile-back")
    def back(self) -> None:
        if self.app.session is not None:
            self.app.switch_screen(MainMenu())

    @on(Button.Pressed, "#profile-exit")
    def quit(self) -> None:
        self.app.action_quit()


class MainMenu(Screen):
    def on_mount(self) -> None:
        self.query_one("#menu-play", Button).focus()

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="main-menu"):
            yield Static("OBSIDIAN ROYALE", id="menu-title")
            yield Static("MENU GŁÓWNE", id="menu-subtitle")
            yield Static("", id="active-player", markup=False)
            yield Button("Gra", id="menu-play")
            yield Button("Sklep", id="menu-shop")
            yield Button("Statystyki", id="menu-stats")
            yield Button("Leaderboard", id="menu-leaderboard")
            yield Button("Ustawienia", id="menu-settings", disabled=True)
            yield Button("Zmień profil", id="menu-profile")
            yield Button("Wyjdź", id="menu-exit")
            yield Static("Ustawienia wkrótce", id="menu-note")

    def on_screen_resume(self) -> None:
        if self.app.session is not None:
            game = self.app.session.game
            self.query_one("#active-player", Static).update(f"Gracz: {game.player.name}")
            self.query_one("#menu-profile", Button).disabled = (
                bool(game.current_bets) or self.app.session.has_pending_round
            )
            self.query_one("#menu-profile", Button).tooltip = "Zmiana profilu wymaga rozliczenia lub usunięcia zakładów."

    @on(Button.Pressed, "#menu-play")
    def play(self) -> None:
        self.app.play()

    @on(Button.Pressed, "#menu-shop")
    def shop(self) -> None:
        self.app.show_shop()

    @on(Button.Pressed, "#menu-stats")
    def statistics(self) -> None:
        self.app.show_statistics()

    @on(Button.Pressed, "#menu-leaderboard")
    def leaderboard(self) -> None:
        self.app.show_leaderboard()

    @on(Button.Pressed, "#menu-profile")
    def change_profile(self) -> None:
        self.app.change_profile()

    @on(Button.Pressed, "#menu-exit")
    def quit(self) -> None:
        self.app.action_quit()
