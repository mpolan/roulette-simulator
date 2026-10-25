from dataclasses import dataclass
from enum import Enum
import random

class PocketColor(Enum):
    RED = "red"
    BLACK = "black"
    GREEN = "green"


@dataclass(frozen=True)
class Pocket:
    number: int
    color: PocketColor


class Wheel:
    def __init__(self) -> None:
        self._pockets: list[Pocket] = []
        self._build_wheel()

    def _build_wheel(self) -> None:
        """Create pockets in European roulette wheel order."""
        self._pockets.append(Pocket(0, PocketColor.GREEN))
        wheel_order = [32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
        red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        
        for n in wheel_order:
            if n in red_numbers:
                self._pockets.append(Pocket(n, PocketColor.RED))
            else:
                self._pockets.append(Pocket(n, PocketColor.BLACK))

    @property
    def pockets(self) -> tuple[Pocket, ...]:
        """Immutable snapshot in European wheel order."""
        return tuple(self._pockets)

    def spin(self) -> Pocket:
        """Return one randomly selected pocket."""
        return random.choice(self._pockets)