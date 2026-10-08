from domain.bet import Bet, BetType

def validate_bet(bet: Bet) -> None:
    amount = bet.amount
    bet_type = bet.bet_type
    selection = bet.selection
    
    if not type(amount) is int:
        raise ValueError("Amount is not an integer")
    
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")
    
    if not type(bet_type) is BetType:
        raise ValueError("Bet type is not BetType")

    if bet_type == BetType.STRAIGHT:
        if not type(selection) is int:
            raise ValueError("Selection must be an integer.")
        if selection not in range (37):
            raise ValueError("Selection not in valid range of numbers")
    else:
        if selection is not None:
            raise ValueError("Selection must be None in BetTypes [ODD, EVEN, RED, BLACK]")