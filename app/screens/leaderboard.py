import sqlite3

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, DataTable, Select, Static
from widgets.badge_label import badge_icon


class LeaderboardScreen(Screen):
    BINDINGS = [("escape", "back", "Menu główne")]

    SORT_OPTIONS = (
        ("Zysk netto", "net_profit"),
        ("Najaktywniejsi — liczba rund", "total_rounds"),
        ("Skuteczność — rundy z zyskiem", "win_rate"),
        ("Kolekcjonerzy — kupione odznaki", "badge_count"),
    )

    def __init__(self, player_id: int) -> None:
        super().__init__()
        self.player_id = player_id

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="leaderboard-panel"):
            yield Static("LEADERBOARD", classes="panel-title")
            yield Select(self.SORT_OPTIONS, value="net_profit", allow_blank=False, id="leaderboard-sort")
            yield Static("", id="leaderboard-rules", classes="panel-hint")
            yield Static("", id="leaderboard-position", markup=False)
            yield DataTable(id="leaderboard-table", cursor_type="row", zebra_stripes=True)
            yield Static("", id="leaderboard-message", markup=False)
            yield Button("Odśwież ranking", id="leaderboard-refresh")
            yield Button("Powrót do menu", id="leaderboard-back")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_column("#", width=4)
        table.add_column("Gracz", width=26)
        table.add_column("Zysk netto", width=14)
        table.add_column("Rundy", width=8)
        table.add_column("Skuteczność", width=13)
        table.add_column("Odznaki", width=8)
        table.add_column("Saldo", width=14)
        self.refresh_leaderboard()
        self.query_one("#leaderboard-sort", Select).focus()

    @on(Select.Changed, "#leaderboard-sort")
    def sort_changed(self, event: Select.Changed) -> None:
        if event.value is not Select.BLANK:
            self.refresh_leaderboard()

    @on(Button.Pressed, "#leaderboard-refresh")
    def refresh_leaderboard(self) -> None:
        sort_by = self.query_one("#leaderboard-sort", Select).value
        table = self.query_one(DataTable)
        # Initial Select.Changed can arrive before the table has its columns.
        if not table.columns:
            return
        table.clear()
        self.query_one("#leaderboard-position", Static).update("")
        message = self.query_one("#leaderboard-message", Static)
        message.remove_class("error-message")
        threshold = self.app.leaderboard.MIN_ROUNDS_FOR_WIN_RATE
        if sort_by == "badge_count":
            rules = "Minimum 1 kupiona odznaka. Największe kolekcje na górze. "
        elif sort_by == "win_rate":
            rules = f"Minimum {threshold} rozegranych rund. "
        else:
            rules = "Minimum 1 rozegrana runda. "
        self.query_one("#leaderboard-rules", Static).update(
            rules + "Ranking lokalny. Saldo nie wpływa na pozycję."
        )
        try:
            entries = self.app.leaderboard.get_leaderboard(sort_by)
        except (sqlite3.Error, OSError, LookupError, ValueError) as error:
            message.add_class("error-message")
            message.update(f"Nie można odczytać rankingu: {error}. Spróbuj odświeżyć.")
            return

        active_position = None
        for position, entry in enumerate(entries, start=1):
            active = entry.player_id == self.player_id
            background = " on #194B40" if active else ""
            emphasis = "bold " if active else ""

            def cell(value: str, color: str = "#F0EDE5") -> Text:
                return Text(value, style=f"{emphasis}{color}{background}", no_wrap=True, overflow="ellipsis")

            rank_color = {1: "#F5D58C", 2: "#C5CFDA", 3: "#D39A71"}.get(position, "#AEBBBE")
            profit_color = "#72F5BA" if entry.net_profit > 0 else "#FF8E9B" if entry.net_profit < 0 else "#F0EDE5"
            player_label = cell("")
            for badge in entry.badges:
                player_label.append_text(badge_icon(badge))
                player_label.append(" ")
            player_label.append(entry.player_name + (" (Ty)" if active else ""))
            table.add_row(
                cell(str(position), rank_color),
                player_label,
                cell(f"{entry.net_profit:+}$", profit_color),
                cell(str(entry.total_rounds)),
                cell(f"{entry.win_rate:.2f}%"),
                cell(str(entry.badge_count)),
                cell(f"{entry.balance}$"),
                key=str(entry.player_id),
            )
            if active:
                active_position = position

        if not entries:
            if sort_by == "badge_count":
                message.update("Brak zakupionych odznak. Pierwszą znajdziesz w Prestige Shop.")
            elif sort_by == "win_rate":
                message.update(f"Brak graczy z co najmniej {threshold} rundami. Zmień kryterium lub rozegraj więcej rund.")
            else:
                message.update("Brak wyników. Rozegraj i zapisz pierwszą rundę, aby pojawić się w rankingu.")
        else:
            message.update(f"Graczy w rankingu: {len(entries)}. Twój profil jest oznaczony jako (Ty).")
        if active_position is not None:
            position_text = f"Twoja pozycja: #{active_position} / {len(entries)}"
        elif sort_by == "badge_count":
            position_text = "Kup odznakę w Prestige Shop, aby dołączyć do rankingu kolekcjonerów."
        elif sort_by == "win_rate":
            position_text = f"Twój profil potrzebuje co najmniej {threshold} rund, aby wejść do tego rankingu."
        else:
            position_text = "Rozegraj pierwszą rundę, aby dołączyć do rankingu."
        self.query_one("#leaderboard-position", Static).update(position_text)
        if table.row_count:
            table.move_cursor(row=0, column=0, scroll=True)

    @on(Button.Pressed, "#leaderboard-back")
    def action_back(self) -> None:
        self.app.pop_screen()
