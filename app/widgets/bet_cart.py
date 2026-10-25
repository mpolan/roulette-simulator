from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Static

from domain.bet import Bet


class RemoveBetButton(Button):
    def __init__(self, bet: Bet) -> None:
        super().__init__("X", classes="remove-bet")
        self.bet = bet


class BetCart(Vertical):
    """Displays accepted bets; only the app may modify the game."""

    class RemoveRequested(Message):
        def __init__(self, bet: Bet) -> None:
            super().__init__()
            self.bet = bet

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bets: tuple[Bet, ...] = ()
        self.total_stake = 0
        self.balance = 0

    def show_bets(self, bets: tuple[Bet, ...], total_stake: int, balance: int) -> None:
        self.bets = bets
        self.total_stake = total_stake
        self.balance = balance
        self.refresh(recompose=True)

    def compose(self) -> ComposeResult:
        yield Static("ACTIVE BETS", classes="cart-title")
        if not self.bets:
            yield Static("No active bets", classes="cart-empty")
        for bet in self.bets:
            with Horizontal(classes="cart-row"):
                selection = f" {bet.selection}" if bet.selection is not None else ""
                yield Static(f"{bet.bet_type.name}{selection}    {bet.amount}$")
                yield RemoveBetButton(bet)
        yield Static(f"TOTAL STAKE: {self.total_stake}$   |   AVAILABLE BALANCE: {self.balance}$",
                     classes="cart-total")

    @on(Button.Pressed, ".remove-bet")
    def remove_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if not self.is_disabled and not event.button.disabled:
            event.button.disabled = True
            self.post_message(self.RemoveRequested(event.button.bet))
