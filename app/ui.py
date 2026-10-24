
from rich.text import Text

from domain.bet import Bet, BetType
from domain.game import Game

from textual.app import App, ComposeResult
from textual.widgets import Button, Static, Header, Input, Select
from textual import on
from textual.containers import Vertical, VerticalScroll
from widgets.roulette_table import RouletteTable
from widgets.roulette_wheel import RouletteWheelView


LINES = """RED
BLACK
EVEN
ODD
STRAIGHT""".splitlines()

BET_TYPE = {
    "RED": BetType.RED,
    "BLACK": BetType.BLACK,
    "EVEN": BetType.EVEN,
    "ODD": BetType.ODD,
    "STRAIGHT": BetType.STRAIGHT,
}


class RouletteApp(App):
    CSS_PATH = "ui.tcss"

    def __init__(self) -> None:
        super().__init__()
        self.game = Game()
        self.animating = False
        self._pending_result = None

    def on_mount(self) -> None:
        self.title = "ROULETTE SIMULATOR"
        self.sub_title = "Obsidian Royale"

        self.spin_btn = self.query_one("#spin", Button)
        self.spin_btn.disabled = True

        self.bet_btn = self.query_one("#bet", Button)
        self.bet_btn.disabled = False

        self.player_bet_display = self.query_one("#player_bet", Static)
        self.player_bet_display.display = False

    def compose(self) -> ComposeResult:
        yield Header()

        with VerticalScroll(id="content"):
            yield Static(f"Balance: {self.game.player.balance}$", id="balance")
            yield Static("No result", id="result")
            yield Static("Your bet", id="player_bet")
            with VerticalScroll(id="table-scroll"):
                yield RouletteTable(self.game.wheel.pockets, id="roulette-table")
            with Vertical(id="bet-form"):
                yield Select(((line, line) for line in LINES), value="RED",
                             allow_blank=False, id="select_bet_type")
                yield Input(placeholder="Choose your number (0-36)", type="integer",
                            id="input_straight_number")
                yield Input(placeholder="Bet amount ($)", type="integer", id="input_bet_amount")
                yield Button("Confirm Bet", id="bet")
            yield RouletteWheelView(self.game.wheel.pockets, id="roulette-wheel")
            yield Button("SPIN", id="spin")

    def lock_betting(self, locked: bool) -> None:
        self.query_one("#bet-form").disabled = locked
        self.query_one(RouletteTable).disabled = locked
        self.bet_btn.disabled = locked

    @on(RouletteTable.NumberSelected)
    def table_selected(self, event: RouletteTable.NumberSelected) -> None:
        if self.animating or self.game.current_bet is not None:
            return
        self.query_one("#select_bet_type", Select).value = "STRAIGHT"
        self.query_one("#input_straight_number", Input).value = str(event.number)

    @on(RouletteTable.OutsideSelected)
    def outside_selected(self, event: RouletteTable.OutsideSelected) -> None:
        if self.animating or self.game.current_bet is not None:
            return
        self.query_one("#select_bet_type", Select).value = event.bet_type.name

    def sync_selection(self) -> None:
        value = self.query_one("#input_straight_number", Input).value
        kind = self.query_one("#select_bet_type", Select).value
        straight = kind == "STRAIGHT"
        self.query_one(RouletteTable).select_outside(None if straight else BET_TYPE.get(kind))
        number = int(value) if straight and value.isdecimal() else None
        self.query_one(RouletteTable).select_number(number if number in range(37) else None)

    @on(Input.Changed, "#input_straight_number")
    def number_changed(self) -> None:
        self.sync_selection()

    @on(Select.Changed, "#select_bet_type")
    def select_changed(self, event: Select.Changed) -> None:
        number_input = self.query_one("#input_straight_number", Input)

        self.sync_selection()
        if event.value == "STRAIGHT":
            number_input.display = True
        else:
            number_input.display = False

    @on(Button.Pressed, "#bet")
    def on_confirm_bet(self, event: Button.Pressed) -> None:
        if self.animating or self.game.current_bet is not None:
            return
        try:
            amount = self.query_one("#input_bet_amount", Input).value
            bet_type = self.query_one("#select_bet_type", Select).value

            if not amount.strip():
                raise ValueError("Please enter a bet amount.")

            if bet_type == "STRAIGHT":
                bet_selection = self.query_one(
                    "#input_straight_number", Input
                ).value

                if not bet_selection.strip():
                    raise ValueError("Please choose a number (0-36).")

                bet = Bet(
                    int(amount),
                    BET_TYPE[bet_type],
                    selection=int(bet_selection)
                )
            else:
                bet = Bet(int(amount), BET_TYPE[bet_type])

            # Game validates and accepts the bet
            self.game.place_bet(bet)

        except ValueError as error:
            self.notify(str(error), severity="error")
            return

        # Update active bet display
        display_text = f"Placed bet: {bet.amount}$ on {bet.bet_type.value}"

        if bet.bet_type == BetType.STRAIGHT:
            display_text += f" - {bet.selection}"

        self.player_bet_display.update(display_text)
        self.player_bet_display.display = True

        # Update buttons
        self.lock_betting(True)
        self.spin_btn.disabled = False

        # Update balance after placing bet
        self.update_balance()

    @on(Button.Pressed, "#spin")
    def on_spin(self, event: Button.Pressed) -> None:
        if self.animating or self.game.current_bet is None:
            return
        try:
            pocket, payout = self.game.spin()
        except ValueError as error:
            self.notify(str(error), severity="error")
            return

        self.animating = True
        self.spin_btn.disabled = True
        self.lock_betting(True)
        self._pending_result = (pocket, payout)
        self.query_one("#result", Static).remove_class("win", "loss", "zero")
        self.query_one("#result", Static).update("Spinning...")
        self.query_one(RouletteWheelView).animate_to(pocket)

    @on(RouletteWheelView.Finished)
    def spin_finished(self, event: RouletteWheelView.Finished) -> None:
        if not self.animating or self._pending_result is None:
            return
        pocket, payout = self._pending_result
        if event.pocket != pocket:
            return
        self._pending_result = None
        self.animating = False
        result_display = self.query_one("#result", Static)
        result_display.remove_class("win", "loss", "zero")
        result_display.add_class("win" if payout > 0 else "loss")
        # Pocket color and bet outcome are independent visual signals.
        result = Text("Result: ")
        color = {"red": "#FF8E9B", "black": "#F0EDE5", "green": "#72F5BA"}[pocket.color.value]
        result.append(f"{pocket.number} ({pocket.color.value.upper()})", style=f"bold {color}")
        status = "WIN" if payout > 0 else "LOSS"
        result.append(f" | {status} | Payout: {payout}$")
        result_display.update(result)

        # Reset UI for next round
        self.spin_btn.disabled = True
        self.lock_betting(False)

        self.player_bet_display.display = False

        # Update balance after spin
        self.update_balance()

    def update_balance(self) -> None:
        balance_display = self.query_one("#balance", Static)

        balance_display.update(
            f"Balance: {self.game.player.balance}$"
        )


if __name__ == "__main__":
    app = RouletteApp()
    app.run()
