from dataclasses import dataclass

@dataclass(frozen=True)
class Badge:
    id: str
    name: str
    price: int
    symbol: str
    description: str