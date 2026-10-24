from rich.text import Text
from textual.message import Message
from textual.timer import Timer
from textual.widgets import Static

from domain.wheel import Pocket


class RouletteWheelView(Static):
    """A fixed pointer over the authentic wheel sequence."""

    class Finished(Message):
        def __init__(self, pocket: Pocket) -> None:
            super().__init__()
            self.pocket = pocket

    def __init__(self, pockets: tuple[Pocket, ...], **kwargs) -> None:
        super().__init__(**kwargs)
        self.pockets = pockets
        self.index = 0
        self.spinning = False
        self._timer: Timer | None = None
        self._remaining = 0
        self._steps = 0
        self._duration = 4.0

    @property
    def current_pocket(self) -> Pocket:
        return self.pockets[self.index]

    def on_mount(self) -> None:
        self.draw_strip()

    def draw_strip(self) -> None:
        strip = Text("                 \u2193\n", style="bold #F5D58C")
        for offset in range(-3, 4):
            pocket = self.pockets[(self.index + offset) % len(self.pockets)]
            background = {"red": "#A92F43", "black": "#17232D",
                          "green": "#17684E"}[pocket.color.value]
            style = f"bold #F0EDE5 on {background}"
            strip.append(f" {pocket.number:2} ", style)
            strip.append(" ")
        strip.append("\n           EUROPEAN WHEEL", style="#E8C477")
        self.update(strip)

    def animate_to(self, pocket: Pocket, duration: float = 4.0) -> None:
        if self.spinning:
            return
        target = self.pockets.index(pocket)
        self._steps = len(self.pockets) * 2 + (target - self.index) % len(self.pockets)
        self._remaining = self._steps
        self._duration = duration
        self.spinning = True
        self._schedule_step()

    def _schedule_step(self) -> None:
        progress = (self._steps - self._remaining) / max(1, self._steps - 1)
        # Normalized increasing delays sum to the requested duration.
        weight_sum = sum(1 + 8 * (i / max(1, self._steps - 1)) ** 3
                         for i in range(self._steps))
        delay = self._duration * (1 + 8 * progress ** 3) / weight_sum
        self._timer = self.set_timer(delay, self._advance)

    def _advance(self) -> None:
        self._timer = None
        if not self.spinning:
            return
        self.index = (self.index + 1) % len(self.pockets)
        self._remaining -= 1
        self.draw_strip()
        if self._remaining:
            self._schedule_step()
        else:
            self.spinning = False
            self.post_message(self.Finished(self.current_pocket))

    def on_unmount(self) -> None:
        self.spinning = False
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
