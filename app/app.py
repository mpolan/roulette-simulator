from domain.wheel import Wheel
from domain.bet import Bet, BetType
wheel = Wheel()

for _ in range(1):
    bet1 = Bet(100, BetType.ODD, None)
    bet2 = Bet(200, BetType.EVEN, None)
    bet3 = Bet(300, BetType.RED, None)
    bet4 = Bet(400, BetType.BLACK, None)
    print(bet1)
    print(bet2)
    print(bet3)
    print(bet4)
    result = wheel.spin()

    print(result.number, " | ", result.color)


