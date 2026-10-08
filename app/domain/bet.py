from dataclasses import dataclass
from enum import Enum

class BetType(Enum):
    STRAIGHT = "straight"
    RED = "red"
    BLACK = "black"
    EVEN = "even"
    ODD = "odd"

@dataclass(frozen=True)
class Bet:
    amount: int
    bet_type: BetType
    selection: int | None = None

    def __str__(self) -> str:
        return (
            f"Bet: {self.amount}$ on {self.bet_type} " 
            f"| selected: {self.selection}"
        )