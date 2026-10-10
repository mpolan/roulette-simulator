from domain.wheel import Wheel
from domain.bet import Bet, BetType
from domain.player import Player
from domain.game import Game

from textual.app import App, ComposeResult
from textual.widgets import Button, Static, Footer, Header, Input

from textual import on
from textual.widgets import Header, Select

LINES = """RED
BLACK
EVEN
ODD
STRAIGHT""".splitlines()

BET_TYPE={
    "RED": BetType.RED,
    "BLACK": BetType.BLACK,
    "EVEN": BetType.EVEN,
    "ODD": BetType.ODD,
    "STRAIGHT": BetType.STRAIGHT,
}

class RouletteApp(App):
    CSS_PATH = "ui.tcss"
    
    def __init__(self):
        super().__init__()
        self.game = Game()

    def on_mount(self) -> None:
        self.bet_choice:str = ""
        self.title = 'ROULETTE APP'
        self.sub_title = ":)"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"Balance: {self.game.player.balance}$", id="balance")

        yield Static("No result", id="result")
        yield Select(((line, line) for line in LINES), value="RED", allow_blank=False, id='select_bet_type')
        yield Input(placeholder="Choose your number", type='integer', id='input_straight_number')
        yield Input(placeholder="Place your bet", type='integer', id='input_bet_amount')
        yield Button("Confirm Bet", id='bet')
        yield Button("SPIN", id='spin')


    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        if event.value == "STRAIGHT":
            self.query_one("#input_straight_number", Input).styles.display='block'
        else:
            self.query_one("#input_straight_number", Input).styles.display='none'


    def on_button_pressed(self, event: Button.Pressed) -> None:
        try:
            if event.button.id == 'bet':
                amount = self.query_one("#input_bet_amount", Input).value
                bet_type = self.query_one("#select_bet_type", Select).value
                if bet_type == "STRAIGHT":
                    bet_selection = self.query_one("#input_straight_number", Input).value
                    bet = Bet(int(amount), BET_TYPE[bet_type], selection=int(bet_selection))
                else:
                    bet = Bet(int(amount), BET_TYPE[bet_type])
                self.game.place_bet(bet)
            elif event.button.id == 'spin':
                pocket, payout = self.game.spin()

                self.query_one("#result", Static).update(
                    f"Result: {pocket.number} ({pocket.color.value}) | Payout: {payout}$"
                )
            self.query_one("#balance", Static).update(
                f"Balance: {self.game.player.balance}$"
            )

        except ValueError as error:
            self.notify(str(error), severity="error")


if __name__ == "__main__":
    app = RouletteApp()
    app.run()