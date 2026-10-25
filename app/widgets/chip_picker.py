from rich.text import Text
from textual.widgets import Button


class ChipButton(Button):
    """A terminal-sized round chip, with a distinct selected rim."""

    COLORS = {5: "#715290", 10: "#943C45", 25: "#217D57", 50: "#285D9A", 100: "#343B47"}

    def __init__(self, value: int, selected: bool = False) -> None:
        super().__init__(f"{value}$", id=f"chip-{value}", classes="chip-choice")
        self.value = value
        self.set_class(selected, "chosen")
        self.tooltip = f"Select {value}$ chip"

    def render(self) -> Text:
        selected = self.has_class("chosen")
        rim = "bold #FFE4A5" if selected else "#B99755"
        fill = f"bold #FFFFFF on {self.COLORS[self.value]}"
        drawing = Text(no_wrap=True)
        for row_index, (prefix, left, inside, right, suffix) in enumerate((
            ("  ", ".", "===" if selected else "---", ".", "  "),
            (" ", "/", "     ", "\\", " "),
            ("", "|", f"{self.value}$".center(7), "|", ""),
            (" ", "\\", "     ", "/", " "),
            ("  ", "'", "===" if selected else "---", "'", "  "),
        )):
            drawing.append(prefix)
            drawing.append(left, rim)
            drawing.append(inside, rim if row_index in (0, 4) else fill)
            drawing.append(right, rim)
            drawing.append(suffix)
            if row_index < 4:
                drawing.append("\n")
        return drawing
