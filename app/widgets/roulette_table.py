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
        def __init__(self, bet_type: BetType, selection: int | None = None) -> None:
            super().__init__()
            self.bet_type = bet_type
            self.selection = selection

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

            with Grid(id="column-bets"):
                for column in (3, 2, 1):
                    yield Button(f"COL {column}", id=f"outside-COLUMN-{column}", classes="outside group")
        with Horizontal(id="dozen-bets"):
            for dozen, label in ((1, "1st 12"), (2, "2nd 12"), (3, "3rd 12")):
                yield Button(label, id=f"outside-DOZEN-{dozen}", classes="outside group")
        with Horizontal(id="outside-bets"):
            for kind in (BetType.LOW, BetType.EVEN, BetType.RED, BetType.BLACK, BetType.ODD, BetType.HIGH):
                yield Button({BetType.LOW: "1-18", BetType.HIGH: "19-36"}.get(kind, kind.name), id=f"outside-{kind.name}",
                             classes=f"outside {kind.value}")

    def select_outside(self, bet_type: BetType | None, selection: int | None = None) -> None:
        selected_id = f"outside-{bet_type.name}" if bet_type is not None else ""
        if selection is not None:
            selected_id += f"-{selection}"
        for button in self.query(".outside"):
            button.set_class(button.id == selected_id, "selected")

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
            parts = event.button.id.split("-")
            self.post_message(self.OutsideSelected(BetType[parts[1]], int(parts[2]) if len(parts) > 2 else None))
            return
        number = int(event.button.id.split("-")[1])
        self.select_numbers(self.selected_numbers ^ {number})
        self.post_message(self.NumbersSelected(self.selected_numbers))
