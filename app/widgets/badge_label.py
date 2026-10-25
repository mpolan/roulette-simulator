from rich.text import Text

from domain.badge import Badge


BADGE_SYMBOL_COLORS = {
    "♥": "#FF8E9B",
    "♦": "#69D7F0",
    "♣": "#72F5BA",
    "♠": "#C49BFF",
    "☻": "#F5D58C",
}


def badge_icon(badge: Badge) -> Text:
    color = BADGE_SYMBOL_COLORS.get(badge.symbol, "#F5D58C")
    return Text(badge.symbol, style=f"bold {color}")


def badge_label(badge: Badge) -> Text:
    label = badge_icon(badge)
    label.append(f"  {badge.name}")
    return label
