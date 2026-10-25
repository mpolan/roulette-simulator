
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Iterator


DB_PATH = Path(__file__).resolve().parents[2] / "data" / "roulette.db"


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                balance INTEGER NOT NULL DEFAULT 1000 CHECK(balance >= 0)
            )
        """)
                
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                winning_number INTEGER NOT NULL CHECK (winning_number BETWEEN 0 AND 36),
                total_stake INTEGER NOT NULL CHECK (total_stake >= 0),
                total_payout INTEGER NOT NULL CHECK (total_payout >= 0),
                net_profit INTEGER NOT NULL,
                played_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS round_bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                round_id INTEGER NOT NULL,
                bet_type TEXT NOT NULL,
                selection INTEGER,
                amount INTEGER NOT NULL CHECK (amount > 0),
                won INTEGER NOT NULL CHECK (won IN (0, 1)),
                payout INTEGER NOT NULL CHECK (payout >= 0),

                FOREIGN KEY (round_id) REFERENCES rounds(id)
            )
        """)
