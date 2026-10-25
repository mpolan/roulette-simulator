import sqlite3

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Static


class StatisticsScreen(Screen):
    BINDINGS = [("escape", "back", "Menu główne")]

    def __init__(self, player_id: int) -> None:
        super().__init__()
        self.player_id = player_id

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="navigation-panel statistics-panel"):
            yield Static("STATYSTYKI GRACZA", classes="panel-title")
            yield Static("", id="stats-player", markup=False)
            yield Static("", id="stats-balance")
            with Vertical(classes="stats-section"):
                yield Static("ROZGRYWKA", classes="section-title")
                yield Static("", id="stats-activity")
            with Vertical(classes="stats-section"):
                yield Static("FINANSE", classes="section-title")
                yield Static("", id="stats-money")
                yield Static("", id="stats-profit")
            with Vertical(classes="stats-section"):
                yield Static("SKUTECZNOŚĆ", classes="section-title")
                yield Static("", id="stats-rates")
            yield Static("Saldo dotyczy ostatniej rozliczonej rundy. Aktywne zakłady nie zmieniają zapisanej historii.", classes="panel-hint")
            yield Static("", id="stats-message", classes="error-message", markup=False)
            yield Button("Odśwież", id="stats-refresh")
            yield Button("Powrót do menu", id="stats-back")

    def on_mount(self) -> None:
        self.refresh_stats()

    @on(Button.Pressed, "#stats-refresh")
    def refresh_stats(self) -> None:
        try:
            profile = self.app.players.get_player(self.player_id)
            if profile is None:
                raise LookupError("Profil nie istnieje.")
            stats = self.app.stats.get_player_stats(self.player_id)
        except (sqlite3.Error, LookupError, ValueError) as error:
            self.query_one("#stats-message", Static).update(f"Nie można odczytać statystyk: {error}")
            return
        self.query_one("#stats-message", Static).update("Brak rozegranych rund." if not stats.total_rounds else "")
        self.query_one("#stats-player", Static).update(profile.name)
        self.query_one("#stats-balance", Static).update(f"Zapisane saldo: {profile.balance}$")
        self.query_one("#stats-activity", Static).update(
            f"Rundy: {stats.total_rounds}\nRundy z zyskiem: {stats.profitable_rounds}\n"
            f"Zakłady: {stats.total_bets}\nWygrane zakłady: {stats.winning_bets}"
        )
        self.query_one("#stats-money", Static).update(
            f"Łączne stawki: {stats.total_stake}$\nŁączne wypłaty: {stats.total_payout}$\n"
            f"Największa wypłata z rundy: {stats.biggest_payout}$"
        )
        color = "#72F5BA" if stats.net_profit > 0 else "#FF8E9B" if stats.net_profit < 0 else "#F0EDE5"
        self.query_one("#stats-profit", Static).update(Text(f"Bilans netto: {stats.net_profit:+}$", style=f"bold {color}"))
        self.query_one("#stats-rates", Static).update(
            f"Rundy z zyskiem: {stats.win_rate:.2f}%\nWygrane zakłady: {stats.bet_win_rate:.2f}%"
        )

    @on(Button.Pressed, "#stats-back")
    def action_back(self) -> None:
        self.app.pop_screen()
