
"""Create a repeatable demonstration database with local player profiles.

Run: python seed_demo.py
Alternative database: python seed_demo.py --db data/demo.db
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
from persistence.shop_repository import ShopRepository
from services.badge_catalog import BadgeCatalog
from services.stats_service import StatsService


class DemoWheel(Wheel):
    """Use a predetermined pocket while retaining the real roulette engine."""

    number = 0

    def spin(self) -> Pocket:
        return next(
            pocket
            for pocket in self.pockets
            if pocket.number == self.number
        )


def red_rounds(
    count: int,
    wins: int,
    amount: int
) -> list[tuple[int, list[Bet]]]:
    return [
        (1 if index < wins else 2, [Bet(amount, BetType.RED)])
        for index in range(count)
    ]


def demo_scenarios() -> list[tuple[str, list[tuple[int, list[Bet]]]]]:
    multi_bets = [
        Bet(10, BetType.EVEN),
        Bet(10, BetType.RED),
        Bet(5, BetType.STRAIGHT, 7),
    ]

    return [
        ("Michal", red_rounds(100, 80, 300)),
        ("Maciek", red_rounds(80, 59, 200)),
        ("Kamil", red_rounds(60, 29, 10)),
        (
            "Gniewko",
            [
                (number, multi_bets)
                for number in (7, 2, 18, 0, 21, 32, 9, 14, 3, 26) * 5
            ],
        ),
        ("Tomek", red_rounds(45, 33, 100)),
        (
            "Kubson",
            [
                (number, [Bet(10, BetType.STRAIGHT, 17)])
                for number in (17, 2, 0, 24, 11, 36) * 8
            ],
        ),
        ("Gdynianin", red_rounds(10, 0, 100)),
        ("Nowy Gracz", []),
    ]


def demo_badges() -> dict[str, tuple[str, ...]]:
    """Badges purchased by demonstration profiles.

    Michal deliberately starts without badges so purchases
    can be demonstrated live.
    """

    return {
        "Maciek": (
            "bronze_roller",
            "silver_roller",
        ),
        "Tomek": (
            "bronze_roller",
        ),
        "Kubson": (
            "bronze_roller",
        ),
    }


def seed_demo(reset: bool = False) -> None:
    database.init_db()

    badge_catalog = BadgeCatalog()
    badges_by_player = demo_badges()

    # One transaction protects all generated profiles,
    # rounds, bets, balances and badge purchases.
    with database.get_connection() as conn:
        occupied = any(
            conn.execute(
                f"SELECT EXISTS(SELECT 1 FROM {table})"
            ).fetchone()[0]
            for table in (
                "players",
                "rounds",
                "round_bets",
                "player_badges",
            )
        )

        if occupied and not reset:
            raise ValueError(
                "Baza zawiera dane. Użyj --reset, aby usunąć "
                "WSZYSTKIE dane i odtworzyć demo, lub --db, "
                "aby wybrać inny plik."
            )

        if reset:
            conn.execute("DELETE FROM player_badges")
            conn.execute("DELETE FROM round_bets")
            conn.execute("DELETE FROM rounds")
            conn.execute("DELETE FROM players")

            conn.execute("""
                DELETE FROM sqlite_sequence
                WHERE name IN (
                    'players',
                    'rounds',
                    'round_bets',
                    'player_badges'
                )
            """)

        start = datetime(2026, 10, 1, 18, 0)

        for profile_index, (name, planned_rounds) in enumerate(
            demo_scenarios()
        ):
            player_id = conn.execute(
                "INSERT INTO players (name) VALUES (?)",
                (name,)
            ).lastrowid

            balance = conn.execute(
                "SELECT balance FROM players WHERE id = ?",
                (player_id,)
            ).fetchone()[0]

            game = Game(Player(name, balance))

            wheel = DemoWheel()
            game.wheel = wheel

            # Generate historical roulette rounds.
            for round_index, (number, bets) in enumerate(planned_rounds):
                wheel.number = number

                game.place_bets(bets)
                result = game.spin()

                played_at = start + timedelta(
                    days=profile_index,
                    minutes=30 * round_index
                )

                round_id = conn.execute("""
                    INSERT INTO rounds (
                        player_id,
                        winning_number,
                        total_stake,
                        total_payout,
                        net_profit,
                        played_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    player_id,
                    result.pocket.number,
                    result.total_stake,
                    result.total_payout,
                    result.net_profit,
                    played_at.isoformat(sep=" "),
                )).lastrowid

                conn.executemany("""
                    INSERT INTO round_bets (
                        round_id,
                        bet_type,
                        selection,
                        amount,
                        won,
                        payout
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [
                    (
                        round_id,
                        item.bet.bet_type.value,
                        item.bet.selection,
                        item.bet.amount,
                        item.won,
                        item.payout,
                    )
                    for item in result.bet_results
                ])

            # Save the balance resulting from roulette.
            conn.execute("""
                UPDATE players
                SET balance = ?
                WHERE id = ?
            """, (
                game.player.balance,
                player_id,
            ))

            # Generate demonstration badge purchases.
            for badge_id in badges_by_player.get(name, ()):
                badge = badge_catalog.get_badge(badge_id)

                if badge is None:
                    raise ValueError(
                        f"Nieznana odznaka demo: {badge_id}"
                    )

                # Purchase only if the player can afford it.
                balance_cursor = conn.execute("""
                    UPDATE players
                    SET balance = balance - ?
                    WHERE id = ?
                      AND balance >= ?
                """, (
                    badge.price,
                    player_id,
                    badge.price,
                ))

                if balance_cursor.rowcount != 1:
                    raise ValueError(
                        f"Gracz {name} nie ma wystarczających "
                        f"środków na odznakę {badge.name}"
                    )

                conn.execute("""
                    INSERT INTO player_badges (
                        player_id,
                        badge_id,
                        price_paid
                    )
                    VALUES (?, ?, ?)
                """, (
                    player_id,
                    badge.id,
                    badge.price,
                ))


def print_summary() -> None:
    stats_service = StatsService(RoundRepository())
    shop_repository = ShopRepository()

    print(f"\nBaza demo: {database.DB_PATH}\n")

    print(
        f"{'Gracz':<16} "
        f"{'Saldo':>9} "
        f"{'Rundy':>7} "
        f"{'Zaklady':>8} "
        f"{'Zysk netto':>12} "
        f"{'Win rate':>10} "
        f"{'Odznaki':>8} "
        f"{'Wydano':>10}"
    )

    print("-" * 90)

    for player in PlayerRepository().get_all_players():
        stats = stats_service.get_player_stats(player.id)
        purchases = shop_repository.get_player_badges(player.id)

        total_spent = sum(
            purchase.price_paid
            for purchase in purchases
        )

        print(
            f"{player.name:<16} "
            f"{player.balance:>8}$ "
            f"{stats.total_rounds:>7} "
            f"{stats.total_bets:>8} "
            f"{stats.net_profit:>+11}$ "
            f"{stats.win_rate:>9.2f}% "
            f"{len(purchases):>8} "
            f"{total_spent:>9}$"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Utwórz profile demo wraz z saldem, historią, "
            "statystykami i zakupionymi odznakami."
        )
    )

    parser.add_argument(
        "--db",
        type=Path,
        help=(
            "Plik SQLite; domyślnie data/roulette.db "
            "w katalogu projektu."
        ),
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help=(
            "Usuń WSZYSTKICH graczy, rundy, zakłady i odznaki "
            "z wybranej bazy przed utworzeniem demo."
        ),
    )

    args = parser.parse_args()

    if args.db is not None:
        database.DB_PATH = args.db.expanduser().resolve()

    try:
        seed_demo(reset=args.reset)
    except (sqlite3.Error, OSError, ValueError) as error:
        parser.exit(
            1,
            f"Nie udało się przygotować bazy demo: {error}\n"
        )

    print_summary()


if __name__ == "__main__":
    main()
