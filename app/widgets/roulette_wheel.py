import math
from time import monotonic

from rich.text import Text
from textual.message import Message
from textual.timer import Timer
from textual.widgets import Static

from domain.wheel import Pocket


class RouletteWheelView(Static):
    """Full European wheel, rotating beneath a stationary pointer."""

    WIDTH = 73
    HEIGHT = 29
    COLORS = {"red": "#A92F43", "black": "#17232D", "green": "#17684E"}

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
        self._position = 0.0
        self._start_position = 0.0
        self._distance = 0
        self._started = 0.0
        self._duration = 7.0
        self._target = 0

    @property
    def current_pocket(self) -> Pocket:
        return self.pockets[self.index]

    def on_mount(self) -> None:
        self.draw_wheel()

    def draw_wheel(self) -> None:
        gold = "#B99755"
        cells = [[(" ", "#F0EDE5") for _ in range(self.WIDTH)]
                 for _ in range(self.HEIGHT)]
        cx, cy = 36, 14

        def put(x: int, y: int, label: str, style: str) -> None:
            for offset, character in enumerate(label):
                if 0 <= x + offset < self.WIDTH and 0 <= y < self.HEIGHT:
                    cells[y][x + offset] = (character, style)

        # Elliptical geometry compensates for terminal cells being taller than wide.
        for radius_x, radius_y, character in ((34, 13, "."), (25, 8, ":"), (19, 6, ".")):
            for step in range(720):
                angle = step * math.tau / 720
                x = round(cx + radius_x * math.sin(angle))
                y = round(cy - radius_y * math.cos(angle))
                put(x, y, character, gold)

        for slot, pocket in enumerate(self.pockets):
            angle = (slot - self._position) * math.tau / len(self.pockets)
            # Small radial dividers between the colored numbered pockets.
            boundary = angle + math.pi / len(self.pockets)
            for radius in (0.77, 0.82, 0.87, 0.92):
                x = round(cx + 34 * radius * math.sin(boundary))
                y = round(cy - 13 * radius * math.cos(boundary))
                put(x, y, ":", gold)
            x = round(cx + 29.5 * math.sin(angle))
            y = round(cy - 10.5 * math.cos(angle))
            style = f"bold #FFFFFF on {self.COLORS[pocket.color.value]}"
            put(x - 1, y, f"{pocket.number:2}", style)

        # A rotating four-armed spindle makes motion visible inside the bowl too.
        for arm in range(4):
            angle = -self._position * math.tau / len(self.pockets) + arm * math.pi / 2
            for step in range(1, 14):
                x = round(cx + step * math.sin(angle))
                y = round(cy - step * 0.36 * math.cos(angle))
                put(x, y, "*" if step == 13 else "+", gold)
        put(cx - 1, cy, "(O)", "bold #F5D58C")
        put(cx - 7, cy + 7, "OBSIDIAN ROYALE", "bold #F5D58C")
        put(cx, 0, "v", "bold #F5D58C")
        put(cx, 1, "|", "bold #F5D58C")
        put(cx, 2, "o", "bold #FFFFFF")
        caption = "SPINNING" if self.spinning else "EUROPEAN WHEEL"
        put(cx - len(caption) // 2, 28, caption, "bold #F5D58C")
        drawing = Text(no_wrap=True, overflow="crop")
        for row_number, row in enumerate(cells):
            for character, style in row:
                drawing.append(character, style)
            if row_number != self.HEIGHT - 1:
                drawing.append("\n")
        self.update(drawing)

    def animate_to(self, pocket: Pocket, duration: float = 7.0) -> None:
        if self.spinning:
            return
        self._target = self.pockets.index(pocket)
        self._start_position = float(self.index)
        self._distance = len(self.pockets) * 4 + (self._target - self.index) % len(self.pockets)
        self._duration = max(0.01, duration)
        self._started = monotonic()
        self.spinning = True
        self.draw_wheel()
        self._timer = self.set_interval(1 / 30, self._advance)

    def _advance(self) -> None:
        if not self.spinning:
            return
        progress = min(1.0, (monotonic() - self._started) / self._duration)
        # Cubic ease-out: rapid revolutions gradually settle onto the engine result.
        eased = 1 - (1 - progress) ** 3
        self._position = self._start_position + self._distance * eased
        self.index = round(self._position) % len(self.pockets)
        finished = progress >= 1
        if finished:
            self._position = float(self._target)
            self.index = self._target
            self.stop_animation()
        self.draw_wheel()
        if finished:
            self.post_message(self.Finished(self.current_pocket))

    def stop_animation(self) -> None:
        self.spinning = False
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def on_unmount(self) -> None:
        self.stop_animation()
