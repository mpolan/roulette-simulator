
from domain.bet import Bet, BetType
from domain.game import Game

from textual.app import App, ComposeResult
from textual.widgets import Button, Static, Header, Input, Select
from textual import on


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

    def on_mount(self) -> None:
        self.title = "ROULETTE APP"
        self.sub_title = ":)"

        self.spin_btn = self.query_one("#spin", Button)
        self.spin_btn.disabled = True

        self.bet_btn = self.query_one("#bet", Button)
        self.bet_btn.disabled = False

        self.player_bet_display = self.query_one("#player_bet", Static)
        self.player_bet_display.display = False

    def compose(self) -> ComposeResult:
        yield Header()

        yield Static(
            f"Balance: {self.game.player.balance}$",
            id="balance"
        )

        yield Static("No result", id="result")
        yield Static("Your bet", id="player_bet")

        yield Select(
            ((line, line) for line in LINES),
            value="RED",
            allow_blank=False,
            id="select_bet_type"
        )

        yield Input(
            placeholder="Choose your number",
            type="integer",
            id="input_straight_number"
        )

        yield Input(
            placeholder="Place your bet",
            type="integer",
            id="input_bet_amount"
        )

        yield Button("Confirm Bet", id="bet")
        yield Button("SPIN", id="spin")

    @on(Select.Changed, "#select_bet_type")
    def select_changed(self, event: Select.Changed) -> None:
        number_input = self.query_one("#input_straight_number", Input)

        if event.value == "STRAIGHT":
            number_input.display = True
        else:
            number_input.display = False

    @on(Button.Pressed, "#bet")
    def on_confirm_bet(self, event: Button.Pressed) -> None:
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
        self.bet_btn.disabled = True
        self.spin_btn.disabled = False

        # Update balance after placing bet
        self.update_balance()

    @on(Button.Pressed, "#spin")
    def on_spin(self, event: Button.Pressed) -> None:
        try:
            pocket, payout = self.game.spin()
            pocket.number = 0
        except ValueError as error:
            self.notify(str(error), severity="error")
            return

        # Result widget
        result_display = self.query_one("#result", Static)

        # Remove styles from previous spin
        result_display.remove_class("win", "loss", "zero")

        # Determine win/loss independently from pocket color
        won = payout > 0
        status = "WIN" if won else "LOSS"

        # Choose visual style
        if pocket.number == 0:
            result_display.add_class("zero")
        elif won:
            result_display.add_class("win")
        else:
            result_display.add_class("loss")

        result_display.update(
            f"Result: {pocket.number} ({pocket.color.value.upper()})"
            f" | {status} | Payout: {payout}$"
        )

        # Reset UI for next round
        self.spin_btn.disabled = True
        self.bet_btn.disabled = False

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
