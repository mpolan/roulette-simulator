from domain.bet import Bet, BetType
from domain.wheel import Pocket, PocketColor

PAYOUT_MULTIPLIERS = {
    BetType.STRAIGHT: 36,
    BetType.RED: 2,
    BetType.BLACK: 2,
    BetType.EVEN: 2,
    BetType.ODD: 2,
    BetType.LOW: 2,
    BetType.HIGH: 2,

    BetType.DOZEN: 3,
    BetType.COLUMN: 3,
}

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
    
    elif bet_type == BetType.LOW:
        return number in range(1, 18 + 1)
    elif bet_type == BetType.HIGH:
        return number in range(19, 36 + 1)
    
    elif bet_type == BetType.DOZEN:
        if selection == 1:
            return number in range(1, 12 + 1)
        if selection == 2:
            return number in range(13, 24 + 1)
        if selection == 3:
            return number in range(25, 36 + 1)
    elif bet_type == BetType.COLUMN:
        if selection == 1:
            return number in [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
        if selection == 2:
            return number in [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35]
        if selection == 3:
            return number in [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36]
    
    return False

def calculate_payout(bet: Bet, won: bool) -> int:
    if not won:
        return 0
    amount = bet.amount
    return amount * PAYOUT_MULTIPLIERS[bet.bet_type]
    
