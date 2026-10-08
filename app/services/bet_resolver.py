from domain.bet import Bet, BetType
from domain.wheel import Pocket, PocketColor

def is_even(n: int) -> bool:
    return n % 2 == 0

def resolve_bet(spin_result: Pocket, bet: Bet) -> bool:
    number = spin_result.number
    spin_color = spin_result.color

    bet_type = bet.bet_type
    selection = bet.selection

    if bet_type == BetType.STRAIGHT:
        return number == selection 
    
    elif bet_type == BetType.RED:
        return spin_color == PocketColor.RED
    elif bet_type == BetType.BLACK:
        return spin_color == PocketColor.BLACK
    
    elif bet_type == BetType.EVEN:
        return number != 0 and is_even(number)
    elif bet_type == BetType.ODD:
        return number != 0 and not is_even(number)
    
    return False

    