from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Button, Header, Input, Select, Static

from domain.bet import Bet, BetType
from domain.game import Game
from domain.round_result import RoundResult
from widgets.bet_cart import BetCart
from widgets.roulette_table import RouletteTable
from widgets.roulette_wheel import RouletteWheelView


BET_TYPE = {kind.name: kind for kind in BetType}


class RouletteApp(App):
    CSS_PATH = "ui.tcss"

    def __init__(self) -> None:
        super().__init__()
        self.game = Game()
        self.animating = False
        self._pending_result: RoundResult | None = None

    def on_mount(self) -> None:
        self.title = "ROULETTE SIMULATOR"
        self.sub_title = "Obsidian Royale"
        self.refresh_bets()
        self.update_draft()

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="content"):
            yield Static(f"Balance: {self.game.player.balance}$", id="balance")
            yield Static("No result", id="result")
            with VerticalScroll(id="table-scroll"):
                yield RouletteTable(self.game.wheel.pockets, id="roulette-table")
            with Vertical(id="bet-form"):
                yield Select(((name, name) for name in BET_TYPE), value="RED",
                             allow_blank=False, id="select_bet_type")
                yield Static("", id="draft-selection")
                yield Input(placeholder="Stake per number / outside bet ($)",
                            type="integer", id="input_bet_amount")
                yield Static("", id="draft-cost")
                yield Button("Confirm Bet", id="bet")
            yield BetCart(id="bet-cart")
            yield RouletteWheelView(self.game.wheel.pockets, id="roulette-wheel")
            yield Button("SPIN", id="spin", disabled=True)

    def lock_betting(self, locked: bool) -> None:
        self.query_one("#bet-form").disabled = locked
        self.query_one(RouletteTable).disabled = locked
        self.query_one(BetCart).disabled = locked
        self.query_one("#spin", Button).disabled = locked or not self.game.current_bets

    def refresh_bets(self) -> None:
        self.query_one("#balance", Static).update(f"Balance: {self.game.player.balance}$")
        self.query_one(BetCart).show_bets(
            self.game.current_bets, self.game.total_stake, self.game.player.balance)
        self.query_one("#spin", Button).disabled = self.animating or not self.game.current_bets

    def update_draft(self) -> None:
        table = self.query_one(RouletteTable)
        kind = self.query_one("#select_bet_type", Select).value
        straight = kind == "STRAIGHT"
        table.select_outside(None if straight else BET_TYPE.get(kind))
        numbers = sorted(table.selected_numbers)
        label = ", ".join(map(str, numbers)) if numbers else "none (click the table)"
        self.query_one("#draft-selection", Static).update(
            f"Selected numbers: {label}" if straight else f"Selected bet: {kind}")
        amount_text = self.query_one("#input_bet_amount", Input).value
        count = len(numbers) if straight else 1
        amount = int(amount_text) if amount_text.isdecimal() else 0
        self.query_one("#draft-cost", Static).update(
            f"Draft cost: {count} x {amount}$ = {count * amount}$ (stake per selection)")

    @on(RouletteTable.NumbersSelected)
    def table_selected(self, event: RouletteTable.NumbersSelected) -> None:
        if self.animating:
            return
        self.query_one("#select_bet_type", Select).value = "STRAIGHT"
        self.update_draft()

    @on(RouletteTable.OutsideSelected)
    def outside_selected(self, event: RouletteTable.OutsideSelected) -> None:
        if not self.animating:
            self.query_one("#select_bet_type", Select).value = event.bet_type.name

    @on(Select.Changed, "#select_bet_type")
    def select_changed(self, event: Select.Changed) -> None:
        if event.value != "STRAIGHT":
            self.query_one(RouletteTable).select_numbers(set())
        self.update_draft()

    @on(Input.Changed, "#input_bet_amount")
    def amount_changed(self) -> None:
        self.update_draft()

    @on(Button.Pressed, "#bet")
    def on_confirm_bet(self, event: Button.Pressed) -> None:
        if self.animating:
            return
        try:
            amount_text = self.query_one("#input_bet_amount", Input).value
            if not amount_text.strip():
                raise ValueError("Please enter a bet amount.")
            amount = int(amount_text)
            kind = BET_TYPE[self.query_one("#select_bet_type", Select).value]
            if kind == BetType.STRAIGHT:
                numbers = sorted(self.query_one(RouletteTable).selected_numbers)
                if not numbers:
                    raise ValueError("Please select at least one number on the table.")
                bets = [Bet(amount, kind, number) for number in numbers]
            else:
                bets = [Bet(amount, kind)]
            self.game.place_bets(bets)
        except ValueError as error:
            self.notify(str(error), severity="error")
            return
        self.query_one(RouletteTable).select_numbers(set())
        self.update_draft()
        self.refresh_bets()
        self.notify(f"Added {len(bets)} bet(s), total stake: {self.game.total_stake}$")

    @on(BetCart.RemoveRequested)
    def remove_bet(self, event: BetCart.RemoveRequested) -> None:
        if self.animating:
            return
        # Ignore stale button events after a cart refresh; identical rows remain independent.
        if not any(bet is event.bet for bet in self.game.current_bets):
            return
        try:
            self.game.remove_bet(event.bet)
        except ValueError as error:
            self.notify(str(error), severity="error")
            return
        self.refresh_bets()

    @on(Button.Pressed, "#spin")
    def on_spin(self, event: Button.Pressed) -> None:
        if self.animating or not self.game.current_bets:
            return
        try:
            result = self.game.spin()
        except ValueError as error:
            self.notify(str(error), severity="error")
            return
        self.animating = True
        self._pending_result = result
        self.lock_betting(True)
        display = self.query_one("#result", Static)
        display.remove_class("win", "loss", "zero")
        display.update("Spinning...")
        self.query_one(RouletteWheelView).animate_to(result.pocket)

    @on(RouletteWheelView.Finished)
    def spin_finished(self, event: RouletteWheelView.Finished) -> None:
        result = self._pending_result
        if not self.animating or result is None or event.pocket != result.pocket:
            return
        self._pending_result = None
        self.animating = False
        display = self.query_one("#result", Static)
        display.remove_class("win", "loss", "zero")
        if result.net_profit != 0:
            display.add_class("win" if result.net_profit > 0 else "loss")
        pocket = result.pocket
        color = {"red": "#FF8E9B", "black": "#F0EDE5", "green": "#72F5BA"}[pocket.color.value]
        text = Text("RESULT: ")
        text.append(f"{pocket.number} {pocket.color.value.upper()}\n", style=f"bold {color}")
        for item in result.bet_results:
            selection = f" {item.bet.selection}" if item.bet.selection is not None else ""
            text.append(f"{item.bet.bet_type.name}{selection} ({item.bet.amount}$)  "
                        f"{'WIN' if item.won else 'LOSS'}  {item.payout:+}$\n",
                        style="#72F5BA" if item.won else "#FF8E9B")
        text.append(f"TOTAL STAKE: {result.total_stake}$\n"
                    f"TOTAL PAYOUT: {result.total_payout}$\n"
                    f"NET PROFIT: {result.net_profit:+}$")
        display.update(text)
        self.query_one(RouletteTable).select_numbers(set())
        self.update_draft()
        self.refresh_bets()
        self.lock_betting(False)


if __name__ == "__main__":
    RouletteApp().run()
