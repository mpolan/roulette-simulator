from textual import events, on
from textual.app import ComposeResult
from textual.containers import Grid, Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button

from domain.bet import Bet, BetType
from domain.wheel import Pocket


class FieldButton(Button):
    """Route mouse clicks ourselves, so Button.Pressed cannot place a second chip."""

    BINDINGS = [("delete", "remove_chip", "Remove chip")]

    class Clicked(Message):
        def __init__(self, button: "FieldButton", mouse_button: int) -> None:
            super().__init__()
            self.button = button
            self.mouse_button = mouse_button

    def __init__(self, label: str, **kwargs) -> None:
        super().__init__(label, **kwargs)
        self.field_label = label

    async def _on_click(self, event: events.Click) -> None:
        event.prevent_default()
        event.stop()
        if not self.is_disabled and event.button in (1, 3):
            self.focus()
            self.post_message(self.Clicked(self, event.button))

    def action_remove_chip(self) -> None:
        if not self.is_disabled:
            self.post_message(self.Clicked(self, 3))


class RouletteTable(Widget):
    """European betting layout; selection never places a bet."""

    class ChipRequested(Message):
        def __init__(self, bet_type: BetType, selection: int | None, remove: bool) -> None:
            super().__init__()
            self.bet_type = bet_type
            self.selection = selection
            self.remove = remove

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
        self.chips_mode = False

    def number_button(self, number: int) -> Button:
        pocket = self.pockets[number]
        return FieldButton(str(number), id=f"number-{number}",
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
                    yield FieldButton(f"COL{column}", id=f"outside-COLUMN-{column}", classes="outside group")
        with Horizontal(id="dozen-bets"):
            for dozen, label in ((1, "1st 12"), (2, "2nd 12"), (3, "3rd 12")):
                yield FieldButton(label, id=f"outside-DOZEN-{dozen}", classes="outside group")
        with Horizontal(id="outside-bets"):
            for kind in (BetType.LOW, BetType.EVEN, BetType.RED, BetType.BLACK, BetType.ODD, BetType.HIGH):
                yield FieldButton({BetType.LOW: "1-18", BetType.HIGH: "19-36"}.get(kind, kind.name), id=f"outside-{kind.name}",
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

    def show_chips(self, stacks: dict[tuple[BetType, int | None], tuple[Bet, ...]], limit: int) -> None:
        for button in self.query(FieldButton):
            key = self.field_key(button)
            stack = stacks.get(key, ())
            button.set_class(bool(stack), "has-chips")
            label = button.field_label
            if stack:
                total = sum(bet.amount for bet in stack)
                label += f"\n{total}$\n@{len(stack)}/{limit}"
            button.label = label
            button.tooltip = f"{button.field_label}: {sum(b.amount for b in stack)}$, {len(stack)}/{limit} chips"

    @staticmethod
    def field_key(button: Button) -> tuple[BetType, int | None]:
        parts = button.id.split("-")
        if parts[0] == "number":
            return BetType.STRAIGHT, int(parts[1])
        return BetType[parts[1]], int(parts[2]) if len(parts) > 2 else None

    def activate_field(self, button: Button, mouse_button: int) -> None:
        if self.is_disabled:
            return
        kind, selection = self.field_key(button)
        if self.chips_mode:
            self.post_message(self.ChipRequested(kind, selection, mouse_button == 3))
        elif mouse_button == 1:
            if kind == BetType.STRAIGHT:
                self.select_numbers(self.selected_numbers ^ {selection})
                self.post_message(self.NumbersSelected(self.selected_numbers))
            else:
                self.post_message(self.OutsideSelected(kind, selection))

    @on(FieldButton.Clicked)
    def field_clicked(self, event: FieldButton.Clicked) -> None:
        event.stop()
        self.activate_field(event.button, event.mouse_button)

    @on(Button.Pressed)
    def number_pressed(self, event: Button.Pressed) -> None:
        # Keyboard Enter/Space uses the same path as one left click.
        event.stop()
        self.activate_field(event.button, 1)
