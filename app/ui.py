from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Grid, Horizontal, HorizontalScroll, Vertical, VerticalScroll
from textual.widgets import Button, Header, Input, Select, Static

from domain.bet import Bet, BetType
from domain.game import Game
from domain.round_result import RoundResult
from widgets.bet_cart import BetCart
from widgets.chip_picker import ChipButton
from widgets.roulette_table import RouletteTable
from widgets.roulette_wheel import RouletteWheelView


BET_TYPE = {kind.name: kind for kind in BetType}


class RouletteApp(App):
    CSS_PATH = "ui.tcss"

    def __init__(self) -> None:
        # Keep the casino palette even when Textual selects its ANSI theme.
        super().__init__(ansi_color=False)
        self.game = Game()
        self.animating = False
        self.chip_value = 25
        self._pending_result: RoundResult | None = None

    def on_mount(self) -> None:
        self.title = "ROULETTE SIMULATOR"
        self.sub_title = "Obsidian Royale"
        self.apply_mode("CHIPS")

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="content"):
            with Horizontal(id="balance-row"):
                yield Static(f"Balance: {self.game.player.balance}$", id="balance")
            with HorizontalScroll(id="table-scroll"):
                yield RouletteTable(self.game.wheel.pockets, id="roulette-table")
            with Horizontal(id="dashboard"):
                with VerticalScroll(id="bet-controls"):
                    with Vertical(id="betting-mode"):
                        yield Select((("CHIPS", "CHIPS"), ("CLASSIC", "CLASSIC")), value="CHIPS",
                                     allow_blank=False, id="select_mode")
                        with Vertical(id="chip-controls"):
                            with Grid(id="chip-picker"):
                                for value in self.game.CHIP_VALUES:
                                    yield ChipButton(value, selected=value == self.chip_value)
                            yield Static("LMB / Enter: add chip\nRMB / Delete: remove last\nMax 5 chips per field")
                    with Vertical(id="bet-form"):
                        yield Select(((name, name) for name in BET_TYPE), value="RED",
                                     allow_blank=False, id="select_bet_type")
                        yield Select(((str(i), i) for i in (1, 2, 3)), value=1,
                                     allow_blank=False, id="select_bet_group")
                        yield Static("", id="draft-selection")
                        yield Input(placeholder="Stake per selection ($)",
                                    type="integer", id="input_bet_amount")
                        yield Static("", id="draft-cost")
                        yield Button("Confirm Bet", id="bet")
                    yield Button("SPIN", id="spin", disabled=True)
                with Vertical(id="round-info"):
                    with VerticalScroll(id="cart-scroll"):
                        yield BetCart(id="bet-cart")
                    with VerticalScroll(id="result-scroll"):
                        yield Static("No result", id="result")
        with VerticalScroll(id="spin-view"):
            with HorizontalScroll(id="wheel-scroll"):
                yield RouletteWheelView(self.game.wheel.pockets, id="roulette-wheel")
            yield Static("", id="spinning-bets")

    def lock_betting(self, locked: bool) -> None:
        self.query_one("#bet-form").disabled = locked
        self.query_one("#betting-mode").disabled = locked
        self.query_one(RouletteTable).disabled = locked
        self.query_one(BetCart).disabled = locked
        self.query_one("#spin", Button).disabled = locked or not self.game.current_bets

    @on(Select.Changed, "#select_mode")
    def mode_changed(self, event: Select.Changed) -> None:
        if self.animating:
            return
        self.apply_mode(event.value)

    def apply_mode(self, mode: str) -> None:
        table = self.query_one(RouletteTable)
        table.chips_mode = mode == "CHIPS"
        table.select_numbers(set())
        self.query_one("#chip-controls").display = table.chips_mode
        self.query_one("#bet-form").display = not table.chips_mode
        self.update_draft()
        self.refresh_bets()

    @on(Button.Pressed, ".chip-choice")
    def chip_selected(self, event: Button.Pressed) -> None:
        if self.animating:
            return
        self.chip_value = event.button.value
        for button in self.query(ChipButton):
            button.set_class(button.value == self.chip_value, "chosen")
            button.refresh()

    @on(RouletteTable.ChipRequested)
    def chip_requested(self, event: RouletteTable.ChipRequested) -> None:
        if self.animating or not self.query_one(RouletteTable).chips_mode:
            return
        try:
            if event.remove:
                self.game.remove_chip(event.bet_type, event.selection)
            else:
                self.game.place_chip(event.bet_type, self.chip_value, event.selection)
        except ValueError as error:
            self.notify(str(error), severity="error")
            return
        self.refresh_bets()

    def refresh_bets(self) -> None:
        stacks = self.game.chip_stacks
        table = self.query_one(RouletteTable)
        table.show_chips(stacks, self.game.MAX_CHIPS_PER_FIELD)
        self.query_one("#balance", Static).update(f"Balance: {self.game.player.balance}$")
        self.query_one(BetCart).show_bets(
            self.game.current_bets, self.game.total_stake, self.game.player.balance)
        self.query_one("#spin", Button).disabled = self.animating or not self.game.current_bets

    def update_draft(self) -> None:
        table = self.query_one(RouletteTable)
        kind = self.query_one("#select_bet_type", Select).value
        straight = kind == "STRAIGHT"
        grouped = kind in ("DOZEN", "COLUMN")
        group = self.query_one("#select_bet_group", Select)
        group.display = grouped
        selection = group.value if grouped else None
        table.select_outside(None if straight or table.chips_mode else BET_TYPE.get(kind), selection)
        numbers = sorted(table.selected_numbers)
        label = ", ".join(map(str, numbers)) if numbers else "none (click the table)"
        self.query_one("#draft-selection", Static).update(
            f"Selected numbers: {label}" if straight else f"Selected bet: {kind}" + (f" {selection}" if grouped else ""))
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
            if event.selection is not None:
                self.query_one("#select_bet_group", Select).value = event.selection
            self.update_draft()

    @on(Select.Changed, "#select_bet_type")
    def select_changed(self, event: Select.Changed) -> None:
        if event.value != "STRAIGHT":
            self.query_one(RouletteTable).select_numbers(set())
        group = self.query_one("#select_bet_group", Select)
        value = group.value
        if event.value == "DOZEN":
            group.set_options((("1st dozen (1-12)", 1), ("2nd dozen (13-24)", 2), ("3rd dozen (25-36)", 3)))
        elif event.value == "COLUMN":
            group.set_options((("Column 1 (1, 4, ... 34)", 1), ("Column 2 (2, 5, ... 35)", 2), ("Column 3 (3, 6, ... 36)", 3)))
        group.value = value if value in (1, 2, 3) else 1
        self.update_draft()

    @on(Select.Changed, "#select_bet_group")
    def group_changed(self) -> None:
        self.update_draft()

    @on(Input.Changed, "#input_bet_amount")
    def amount_changed(self) -> None:
        self.update_draft()

    @on(Button.Pressed, "#bet")
    def on_confirm_bet(self, event: Button.Pressed) -> None:
        if self.animating or self.query_one(RouletteTable).chips_mode:
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
            elif kind in (BetType.DOZEN, BetType.COLUMN):
                selection = self.query_one("#select_bet_group", Select).value
                if selection not in (1, 2, 3):
                    raise ValueError("Please select a dozen or column (1-3).")
                bets = [Bet(amount, kind, selection)]
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
        display.remove_class("win", "loss")
        display.update("Spinning...")
        # Use the accepted bets in the result: the engine has already cleared its cart.
        lines = ["BETS IN THIS ROUND"]
        field_totals: dict[tuple[BetType, int | None], int] = {}
        for item in result.bet_results:
            bet = item.bet
            key = (bet.bet_type, bet.selection)
            field_totals[key] = field_totals.get(key, 0) + bet.amount
        for (kind, number), amount in field_totals.items():
            selection = f" {number}" if number is not None else ""
            lines.append(f"{kind.name}{selection}    {amount}$")
        lines.append(f"TOTAL STAKE: {result.total_stake}$")
        self.query_one("#spinning-bets", Static).update("\n".join(lines))
        self.screen.add_class("spinning")
        self.query_one("#spin-view", VerticalScroll).scroll_home(animate=False)
        self.query_one("#spin-view").focus()
        self.query_one(RouletteWheelView).animate_to(result.pocket)

    @on(RouletteWheelView.Finished)
    def spin_finished(self, event: RouletteWheelView.Finished) -> None:
        result = self._pending_result
        if not self.animating or result is None or event.pocket != result.pocket:
            return
        self._pending_result = None
        self.animating = False
        display = self.query_one("#result", Static)
        display.remove_class("win", "loss")
        if result.net_profit != 0:
            display.add_class("win" if result.net_profit > 0 else "loss")
        pocket = result.pocket
        color = {"red": "#FF8E9B", "black": "#F0EDE5", "green": "#72F5BA"}[pocket.color.value]
        text = Text("RESULT: ")
        text.append(f"{pocket.number} {pocket.color.value.upper()}\n", style=f"bold {color}")
        for item in result.bet_results:
            selection = f" {item.bet.selection}" if item.bet.selection is not None else ""
            text.append(f"{item.bet.bet_type.name}{selection} ({item.bet.amount}$)  "
                        f"{'WIN' if item.won else 'LOSS'}  PAYOUT: {item.payout}$\n",
                        style="#72F5BA" if item.won else "#FF8E9B")
        text.append(f"\nTOTAL STAKE: {result.total_stake}$\n"
                    f"TOTAL PAYOUT (includes returned winning stakes): {result.total_payout}$\n",
                    style="#F0EDE5")
        outcome = "PROFIT" if result.net_profit > 0 else "LOSS" if result.net_profit < 0 else "BREAK EVEN"
        net_color = "#72F5BA" if result.net_profit > 0 else "#FF8E9B" if result.net_profit < 0 else "#F0EDE5"
        text.append(f"NET PROFIT (payout - stake): {result.net_profit:+}$ | {outcome}",
                    style=f"bold {net_color}")
        display.update(text)
        self.query_one(RouletteTable).select_numbers(set())
        self.update_draft()
        self.refresh_bets()
        self.lock_betting(False)
        self.screen.remove_class("spinning")
        self.query_one("#content", VerticalScroll).scroll_home(animate=False)
        self.query_one("#result-scroll", VerticalScroll).scroll_home(animate=False)
        self.query_one(f"#chip-{self.chip_value}" if self.query_one(RouletteTable).chips_mode else "#select_bet_type").focus()


if __name__ == "__main__":
    RouletteApp().run()
