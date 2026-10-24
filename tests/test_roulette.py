import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from domain.bet import Bet, BetType
from domain.game import Game
from domain.wheel import Wheel, PocketColor
from ui import RouletteApp
from widgets.roulette_table import RouletteTable
from widgets.roulette_wheel import RouletteWheelView
from textual.widgets import Input, Select, Static, Button


class WheelTests(unittest.TestCase):
    def test_mapping(self):
        pockets = Wheel().pockets
        self.assertIsInstance(pockets, tuple)
        self.assertEqual({p.number for p in pockets}, set(range(37)))
        reds = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
        self.assertEqual({p.number for p in pockets if p.color == PocketColor.RED}, reds)
        self.assertEqual([p.number for p in pockets[:5]], [0,32,15,19,4])

    def test_zero_and_single_settlement(self):
        for kind in BetType:
            game = Game()
            game.wheel.spin = Mock(return_value=game.wheel.pockets[0])
            game.place_bet(Bet(10, kind, 0 if kind == BetType.STRAIGHT else None))
            pocket, payout = game.spin()
            self.assertEqual(payout, 360 if kind == BetType.STRAIGHT else 0)
            balance = game.player.balance
            with self.assertRaises(ValueError):
                game.spin()
            self.assertEqual(game.player.balance, balance)
            game.wheel.spin.assert_called_once()


class UITests(unittest.IsolatedAsyncioTestCase):
    async def test_table_colors_and_outside_bets(self):
        app = RouletteApp()
        async with app.run_test(size=(100, 50)) as pilot:
            from textual.color import Color
            for number, color in ((1, '#A92F43'), (2, '#121D27'), (0, '#17684E')):
                self.assertEqual(app.query_one(f'#number-{number}').styles.background, Color.parse(color))
            for name in ('RED', 'BLACK', 'EVEN', 'ODD'):
                await pilot.click(f'#outside-{name}')
                await pilot.pause()
                self.assertEqual(app.query_one(Select).value, name)
                self.assertTrue(app.query_one(f'#outside-{name}').has_class('selected'))
                self.assertIsNone(app.query_one(RouletteTable).selected_number)
                self.assertEqual(app.game.player.balance, 1000)
                self.assertIsNone(app.game.current_bet)
            app.query_one('#input_bet_amount', Input).value = '10'
            app.on_confirm_bet(None)
            self.assertTrue(app.query_one('#outside-RED').is_disabled)

    async def test_rounds(self):
        app = RouletteApp()
        async with app.run_test(size=(100, 50)) as pilot:
            table = app.query_one(RouletteTable)
            self.assertEqual(len(table.query(".pocket")), 37)
            self.assertEqual([int(b.label.plain) for b in table.query('#number-grid Button')][:12], list(range(3,37,3)))
            await pilot.click('#number-17')
            await pilot.pause()
            self.assertEqual(app.query_one(Select).value, 'STRAIGHT')
            self.assertEqual(app.query_one('#input_straight_number', Input).value, '17')
            self.assertEqual(app.game.player.balance, 1000)
            wheel = app.query_one(RouletteWheelView)
            animate = wheel.animate_to
            wheel.animate_to = lambda pocket: animate(pocket, duration=0.15)
            app.game.spin = Mock(wraps=app.game.spin)
            for number in (17, 0):
                app.query_one('#input_straight_number', Input).value = str(number)
                app.query_one('#input_bet_amount', Input).value = '10'
                await pilot.pause()
                target = next(p for p in app.game.wheel.pockets if p.number == number)
                app.game.wheel.spin = Mock(return_value=target)
                app.on_confirm_bet(None)
                balance_text = str(app.query_one('#balance', Static).render())
                app.on_confirm_bet(None)
                app.on_spin(None)
                app.on_spin(None)
                self.assertTrue(table.disabled)
                self.assertEqual(str(app.query_one('#balance', Static).render()), balance_text)
                await pilot.pause(2)
                self.assertFalse(app.animating)
                self.assertEqual(wheel.current_pocket, target)
                self.assertIsNone(wheel._timer)
                self.assertFalse(table.disabled)
                self.assertIsNone(app.game.current_bet)
            self.assertEqual(app.game.spin.call_count, 2)
            self.assertEqual(app.game.player.balance, 1700)

    async def test_keyboard_and_timer_cleanup(self):
        app = RouletteApp()
        async with app.run_test(size=(60, 30)) as pilot:
            button = app.query_one('#number-0', Button)
            button.focus()
            await pilot.press('enter')
            await pilot.pause()
            self.assertEqual(app.query_one(Select).value, 'STRAIGHT')
            self.assertEqual(app.query_one(RouletteTable).selected_number, 0)
            wheel = app.query_one(RouletteWheelView)
            wheel.animate_to(wheel.pockets[5])
            self.assertTrue(wheel.spinning)
            self.assertIsNotNone(wheel._timer)
        self.assertFalse(wheel.spinning)
        self.assertIsNone(wheel._timer)

    async def test_every_animation_target(self):
        app = RouletteApp()
        async with app.run_test(size=(60, 30)):
            wheel = app.query_one(RouletteWheelView)
            wheel._schedule_step = lambda: None
            for target in wheel.pockets:
                wheel.animate_to(target)
                while wheel.spinning:
                    wheel._advance()
                self.assertEqual(wheel.current_pocket, target)


if __name__ == '__main__':
    unittest.main()

