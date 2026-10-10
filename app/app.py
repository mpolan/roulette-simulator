from domain.wheel import Wheel
from domain.bet import Bet, BetType
from domain.player import Player
from domain.game import Game


game = Game()

print("\n========== 1. INICJALIZACJA ==========")
print(f"Gracz:             {game.player.name}")
print(f"Saldo początkowe:  {game.player.balance}$")
print(f"Aktywny zakład:    {game.current_bet}")
print(f"Koło:              {type(game.wheel).__name__}")


print("\n========== 2. STAWIANIE ZAKŁADU ==========")
bet = Bet(250, BetType.ODD)

print(f"Stawka:            {bet.amount}$")
print(f"Typ zakładu:       {bet.bet_type.value}")
print(f"Wybór:             {bet.selection}")

game.place_bet(bet)

print(f"Saldo po zakładzie: {game.player.balance}$")
print(f"Aktywny zakład:     {game.current_bet}")


print("\n========== 3. LOSOWANIE ==========")
spin_result, payout = game.spin()

print(f"Wylosowany numer:  {spin_result.number}")
print(f"Kolor pola:        {spin_result.color.value}")
print(f"Wynik zakładu:     {'WYGRANA' if payout > 0 else 'PRZEGRANA'}")
print(f"Całkowita wypłata: {payout}$")


print("\n========== 4. PODSUMOWANIE ==========")
print(f"Saldo końcowe:     {game.player.balance}$")
print(f"Bilans rundy:      {payout - bet.amount:+}$")
print(f"Aktywny zakład:    {game.current_bet}")
print("======================================\n")