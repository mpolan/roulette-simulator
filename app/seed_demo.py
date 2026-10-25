"""Create a repeatable demonstration database with eight local player profiles.

Run: python seed_demo.py
Alternative file: python seed_demo.py --db data/demo.db
Replace ALL existing data: python seed_demo.py --reset
The default database is the same one used by python app/app.py.
"""

import argparse
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "app"))

from domain.bet import Bet, BetType
from domain.game import Game
from domain.player import Player
from domain.wheel import Pocket, Wheel
from persistence import database
from persistence.player_repository import PlayerRepository
from persistence.round_repository import RoundRepository
from services.stats_service import StatsService


class DemoWheel(Wheel):
    """Use a predetermined pocket while retaining the real roulette engine."""

    number = 0

    def spin(self) -> Pocket:
        return next(pocket for pocket in self.pockets if pocket.number == self.number)


def red_rounds(count: int, wins: int, amount: int) -> list[tuple[int, list[Bet]]]:
    return [(1 if index < wins else 2, [Bet(amount, BetType.RED)]) for index in range(count)]


def demo_scenarios() -> list[tuple[str, list[tuple[int, list[Bet]]]]]:
    multi_bets = [Bet(10, BetType.EVEN), Bet(10, BetType.RED), Bet(5, BetType.STRAIGHT, 7)]
    return [
        ("Michal", red_rounds(30, 20, 25)),
        ("Maciek", red_rounds(18, 14, 50)),
        ("Kamil", red_rounds(60, 29, 10)),
        ("Gniewko", [(number, multi_bets) for number in (7, 2, 18, 0, 21, 32, 9, 14, 3, 26) * 2]),
        ("Tomek", red_rounds(12, 10, 25)),
        ("Kubson", [(number, [Bet(10, BetType.STRAIGHT, 17)]) for number in (17, 2, 0, 24, 11, 36)]),
        ("Gdynianin", red_rounds(10, 0, 100)),
        ("Nowy Gracz", []),
    ]


def seed_demo(reset: bool = False) -> None:
    database.init_db()
    # One transaction also protects existing data if replacement fails midway.
    with database.get_connection() as conn:
        occupied = any(
            conn.execute(f"SELECT EXISTS(SELECT 1 FROM {table})").fetchone()[0]
            for table in ("players", "rounds", "round_bets", "player_badges")
        )
        if occupied and not reset:
            raise ValueError("Baza zawiera dane. Użyj --reset, aby usunąć WSZYSTKIE dane i odtworzyć demo, lub --db, aby wybrać inny plik.")
        if reset:
            conn.execute("DELETE FROM player_badges")
            conn.execute("DELETE FROM round_bets")
            conn.execute("DELETE FROM rounds")
            conn.execute("DELETE FROM players")
            conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('players', 'rounds', 'round_bets', 'player_badges')")

        start = datetime(2026, 10, 1, 18, 0)
        for profile_index, (name, planned_rounds) in enumerate(demo_scenarios()):
            # The initial balance comes from the actual database default.
            player_id = conn.execute("INSERT INTO players (name) VALUES (?)", (name,)).lastrowid
            balance = conn.execute("SELECT balance FROM players WHERE id = ?", (player_id,)).fetchone()[0]
            game = Game(Player(name, balance))
            wheel = DemoWheel()
            game.wheel = wheel

            for round_index, (number, bets) in enumerate(planned_rounds):
                wheel.number = number
                game.place_bets(bets)
                result = game.spin()
                played_at = start + timedelta(days=profile_index, minutes=30 * round_index)
                round_id = conn.execute("""
                    INSERT INTO rounds
                        (player_id, winning_number, total_stake, total_payout, net_profit, played_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (player_id, result.pocket.number, result.total_stake,
                      result.total_payout, result.net_profit, played_at.isoformat(sep=" "))).lastrowid
                conn.executemany("""
                    INSERT INTO round_bets (round_id, bet_type, selection, amount, won, payout)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [(round_id, item.bet.bet_type.value, item.bet.selection,
                       item.bet.amount, item.won, item.payout) for item in result.bet_results])

            conn.execute("UPDATE players SET balance = ? WHERE id = ?", (game.player.balance, player_id))


def print_summary() -> None:
    stats_service = StatsService(RoundRepository())
    print(f"Baza demo: {database.DB_PATH}")
    print(f"{'Gracz':<16} {'Saldo':>8} {'Rundy':>7} {'Zaklady':>8} {'Zysk netto':>12} {'Win rate':>10}")
    for player in PlayerRepository().get_all_players():
        stats = stats_service.get_player_stats(player.id)
        print(f"{player.name:<16} {player.balance:>7}$ {stats.total_rounds:>7} "
              f"{stats.total_bets:>8} {stats.net_profit:>+11}$ {stats.win_rate:>9.2f}%")


def main() -> None:
    parser = argparse.ArgumentParser(description="Utwórz 8 profili demo wraz z saldem, historią i statystykami.")
    parser.add_argument("--db", type=Path, help="Plik SQLite; domyślnie data/roulette.db w katalogu projektu.")
    parser.add_argument("--reset", action="store_true", help="Usuń WSZYSTKICH graczy, rundy i zakłady z wybranej bazy przed utworzeniem demo.")
    args = parser.parse_args()
    if args.db is not None:
        database.DB_PATH = args.db.expanduser().resolve()
    try:
        seed_demo(reset=args.reset)
    except (sqlite3.Error, OSError, ValueError) as error:
        parser.exit(1, f"Nie udało się przygotować bazy demo: {error}\n")
    print_summary()


if __name__ == "__main__":
    main()
