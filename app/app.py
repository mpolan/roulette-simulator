from domain.wheel import Wheel
from domain.bet import Bet, BetType

from services.bet_resolver import resolve_bet
wheel = Wheel()

# for _ in range(1):
#     
#     bet2 = Bet(200, BetType.EVEN, None)
#     bet3 = Bet(300, BetType.RED, None)
#     bet4 = Bet(400, BetType.BLACK, None)
#     print(bet1)
#     print(bet2)
#     print(bet3)
#     print(bet4)
#     result = wheel.spin()

#     print(result.number, " | ", result.color)

bet1 = Bet(100, BetType.ODD, None)
bet2 = Bet(200, BetType.EVEN, None)
bet3 = Bet(300, BetType.RED, None)
bet4 = Bet(400, BetType.BLACK, None)
bet5 = Bet(500, BetType.STRAIGHT, 10)
result = wheel.spin()

while result.number != 0:
    result = wheel.spin()


print(result.number, " | ", result.color)
print(bet1, " || ", resolve_bet(result, bet1))
print(bet2, " || ", resolve_bet(result, bet2))
print(bet3, " || ", resolve_bet(result, bet3))
print(bet4, " || ", resolve_bet(result, bet4))
print(bet5, " || ", resolve_bet(result, bet5))




