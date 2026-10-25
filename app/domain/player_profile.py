from dataclasses import dataclass

@dataclass(frozen=True)
class PlayerProfile:
    id: int
    name: str