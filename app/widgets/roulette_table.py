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

    class NumbersSelected(Message):
        def __init__(self, numbers: set[int]) -> None:
            super().__init__()
            self.numbers = frozenset(numbers)

    class OutsideSelected(Message):
        def __init__(self, bet_type: BetType) -> None:
            super().__init__()
            self.bet_type = bet_type

    def __init__(self, pockets: tuple[Pocket, ...], **kwargs) -> None:
        super().__init__(**kwargs)
        self.pockets = {p.number: p for p in pockets}
        self.selected_numbers: set[int] = set()

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

    def select_numbers(self, numbers: set[int]) -> None:
        self.selected_numbers = set(numbers)
        for button in self.query(".pocket"):
            button.set_class(int(button.id.split("-")[1]) in self.selected_numbers, "selected")

    @on(Button.Pressed)
    def number_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if self.disabled:
            return
        if event.button.has_class("outside"):
            self.post_message(self.OutsideSelected(BetType[event.button.id.split("-")[1]]))
            return
        number = int(event.button.id.split("-")[1])
        self.select_numbers(self.selected_numbers ^ {number})
        self.post_message(self.NumbersSelected(self.selected_numbers))
