import io
import unittest
from unittest.mock import Mock, patch

from rich.console import Console

from src.wordies import Wordies


class WordiesCliInteractionTests(unittest.TestCase):
    def make_game(self) -> Wordies:
        console = Console(file=io.StringIO(), force_terminal=False, color_system=None)
        return Wordies(["apple"], console=console)

    def test_process_menu_commands_update_ui_state(self) -> None:
        game = self.make_game()

        game.process_menu("*menu")
        self.assertEqual(game.status_message, "Commands: *menu, *clue, *debug, *quit")
        self.assertEqual(game.status_kind, "info")

        game.process_menu("*clue")
        self.assertTrue(game.show_clue)
        self.assertEqual(game.status_message, "Clue mode enabled.")

        game.process_menu("*debug")
        self.assertTrue(game.show_debug)
        self.assertEqual(game.status_message, "Debug mode enabled.")

        game.process_menu("*wat")
        self.assertEqual(game.status_kind, "error")
        self.assertEqual(game.status_message, "Unknown command. Type *menu to see the options.")

    def test_quit_command_exits_cleanly(self) -> None:
        game = self.make_game()
        with patch.object(game.console, "print") as console_print:
            with self.assertRaises(SystemExit):
                game.process_menu("*quit")
        console_print.assert_called_once()

    def test_start_handles_commands_then_wins_round(self) -> None:
        game = self.make_game()
        game.render = Mock()
        prompts = iter(["*menu", "*clue", "*debug", "ab1de", "apple"])

        with patch.object(game, "prompt_for_guess", side_effect=lambda: next(prompts)):
            with patch("src.wordies.Confirm.ask", return_value=False):
                game.start()

        self.assertTrue(game.show_clue)
        self.assertTrue(game.show_debug)
        self.assertEqual(game.completed_games_guesses, [1])
        self.assertEqual(game.status_message, "You won in 1 guesses.")
        self.assertGreaterEqual(game.render.call_count, 1)
