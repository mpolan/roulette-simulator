"""Sprawdzenie niezależności punktów wejścia w świeżych procesach."""

import os
import subprocess
import sys
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1] / "app"


def run_isolated(code, cwd):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(APP_ROOT)
    prelude = """
from pathlib import Path
from persistence import database
database.DB_PATH = Path.cwd() / 'subprocess.db'
"""
    check_no_write = "\nassert not database.DB_PATH.exists(), 'Import unexpectedly wrote a database'\n"
    return subprocess.run(
        [sys.executable, "-c", prelude + code + check_no_write], cwd=cwd, env=env,
        capture_output=True, text=True, timeout=30,
    )


def test_core_imports_without_terminal_or_qt_packages(tmp_path):
    result = run_isolated("""
import importlib.abc
import sys
class BlockPresentation(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'textual', 'rich', 'PySide6'}:
            raise ImportError('Presentation package forbidden: ' + fullname)
sys.meta_path.insert(0, BlockPresentation())
from domain.bet import Bet, BetType
from domain.game import Game
from domain.player import Player
from services.session_factory import create_game_session
from services.stats_service import StatsService
from services.leaderboard_service import LeaderboardService
from services.shop_service import ShopService
game = Game(Player())
bet = Bet(5, BetType.RED)
game.place_bet(bet)
assert game.current_bets[0] is bet
assert game.player.balance == 995
assert not {'textual', 'rich', 'PySide6'}.intersection(sys.modules)
""", tmp_path)
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "subprocess.db").exists()


def test_tui_entry_imports_without_qt(tmp_path):
    result = run_isolated("""
import importlib.abc
import runpy
import sys
class BlockQt(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] == 'PySide6':
            raise ImportError('Qt forbidden in TUI')
sys.meta_path.insert(0, BlockQt())
runpy.run_module('app', run_name='tui_import_probe')
assert 'ui' in sys.modules
assert 'PySide6' not in sys.modules
""", tmp_path)
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "subprocess.db").exists()


def test_gui_entry_import_has_no_tui_or_database_side_effects(tmp_path):
    result = run_isolated("""
import importlib.abc
from pathlib import Path
import sys
class BlockTerminal(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'textual', 'rich', 'ui', 'screens', 'widgets'}:
            raise ImportError('Terminal presentation forbidden: ' + fullname)
sys.meta_path.insert(0, BlockTerminal())
from persistence import database
database.DB_PATH = Path.cwd() / 'probe.db'
import gui_app
assert not database.DB_PATH.exists()
assert 'ui' not in sys.modules
assert 'textual' not in sys.modules
assert 'PySide6.QtWidgets' in sys.modules
""", tmp_path)
    assert result.returncode == 0, result.stderr


def test_gui_script_entry_runs_with_original_import_layout(tmp_path):
    result = run_isolated(f"""
from pathlib import Path
import runpy
from persistence import database
from gui import application
database.DB_PATH = Path.cwd() / 'entry.db'
called = []
application.run = lambda: called.append(True) or 0
try:
    runpy.run_path({str(APP_ROOT / 'gui_app.py')!r}, run_name='__main__')
except SystemExit as error:
    assert error.code == 0
assert called == [True]
assert not database.DB_PATH.exists()
""", tmp_path)
    assert result.returncode == 0, result.stderr
