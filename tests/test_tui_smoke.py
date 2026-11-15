"""Uruchomienie istniejącego TUI w trybie testowym Textual, bez terminala."""

import asyncio
import runpy
from pathlib import Path

from textual.widgets import Button, Input

from domain.bet import BetType
from persistence.player_repository import PlayerRepository
from screens.game import GameScreen
from screens.navigation import MainMenu, ProfileScreen
from ui import RouletteApp


def test_original_entrypoint_profiles_game_and_session_guards(monkeypatch, isolated_db_path):
    visited = []

    async def exercise(app):
        async with app.run_test(size=(160, 60)) as pilot:
            await pilot.pause()
            assert isinstance(app.screen, ProfileScreen)
            app.screen.query_one("#profile-name", Input).value = "  Gracz testowy  "
            await pilot.click("#profile-create")
            await pilot.pause()
            assert isinstance(app.screen, MainMenu)
            assert app.session.game.player.name == "Gracz testowy"
            assert app.session.game.player.balance == 1000
            session = app.session
            await pilot.click("#menu-play")
            await pilot.pause()
            assert isinstance(app.screen, GameScreen)
            app.session.game.place_chip(BetType.RED, 25)
            app.screen.refresh_bets()
            assert not app.screen.query_one("#spin", Button).disabled
            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(app.screen, MainMenu)
            app.change_profile()
            app.action_quit()
            await pilot.pause()
            assert isinstance(app.screen, MainMenu)
            assert app.session is session
            assert session.game.player.balance == 975
            session.game.remove_chip(BetType.RED)
            app.change_profile()
            await pilot.pause()
            assert isinstance(app.screen, ProfileScreen)
            assert app.session is session
            visited.append(True)

    monkeypatch.setattr(RouletteApp, "run", lambda self: asyncio.run(exercise(self)))
    entry = Path(__file__).resolve().parents[1] / "app/app.py"
    runpy.run_path(str(entry), run_name="__main__")
    assert visited == [True]
    assert isolated_db_path.exists()
    assert len(PlayerRepository().get_all_players()) == 1
