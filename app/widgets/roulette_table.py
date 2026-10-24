from textual import on
from textual.app import ComposeResult
from textual.containers import Grid, Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button

from domain.bet import BetType
from domain.wheel import Pocket


class RouletteTable(Widget):
    """European betting layout; selection never places a bet."""

    class NumberSelected(Message):
        def __init__(self, number: int) -> None:
            super().__init__()
            self.number = number

    class OutsideSelected(Message):
        def __init__(self, bet_type: BetType) -> None:
            super().__init__()
            self.bet_type = bet_type

    def __init__(self, pockets: tuple[Pocket, ...], **kwargs) -> None:
        super().__init__(**kwargs)
        self.pockets = {p.number: p for p in pockets}
        self.selected_number: int | None = None

    def number_button(self, number: int) -> Button:
        pocket = self.pockets[number]
        return Button(str(number), id=f"number-{number}",
                      classes=f"pocket {pocket.color.value}")

    def compose(self) -> ComposeResult:
        with Horizontal(id="table-layout"):
            yield self.number_button(0)
            with Grid(id="number-grid"):
                for row in (3, 2, 1):
                    for number in range(row, 37, 3):
                        yield self.number_button(number)

        with Horizontal(id="outside-bets"):
            for kind in (BetType.RED, BetType.BLACK, BetType.EVEN, BetType.ODD):
                yield Button(kind.name, id=f"outside-{kind.name}",
                             classes=f"outside {kind.value}")

    def select_outside(self, bet_type: BetType | None) -> None:
        for button in self.query(".outside"):
            button.set_class(bet_type is not None and button.id == f"outside-{bet_type.name}", "selected")

    def select_number(self, number: int | None) -> None:
        self.selected_number = number
        for button in self.query(".pocket"):
            button.set_class(button.id == f"number-{number}", "selected")

    @on(Button.Pressed)
    def number_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if self.disabled:
            return
        if event.button.has_class("outside"):
            self.post_message(self.OutsideSelected(BetType[event.button.id.split("-")[1]]))
            return
        number = int(event.button.id.split("-")[1])
        self.select_number(number)
        self.post_message(self.NumberSelected(number))
