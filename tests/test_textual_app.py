import io
import json
import tempfile
import unittest
from pathlib import Path

from rich.console import Console
from textual.widgets import Button, Input

from src.textual_app import WordiesTextualApp


class WordiesTextualAppTests(unittest.IsolatedAsyncioTestCase):
    def build_app(self, history_path: Path) -> WordiesTextualApp:
        return WordiesTextualApp(
            ["apple"],
            history_path=history_path,
            animation_delay=0,
            celebration_duration=0,
        )

    async def test_command_buttons_and_guess_submission(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = self.build_app(Path(temp_dir) / "history.json")

            async with app.run_test(size=(140, 40)) as pilot:
                await pilot.pause()
                await pilot.click("#clue-button")
                await pilot.pause()
                self.assertTrue(app.show_clue)

                await pilot.click("#debug-button")
                await pilot.pause()
                self.assertTrue(app.show_debug)

                app.submit_text("ab1de")
                await pilot.pause()
                self.assertEqual(app.status_message, "Word must only contain letters A-Z.")

                app.submit_text("apple")
                await pilot.pause()
                self.assertEqual(app.status_message, "You won in 1 guesses.")
                self.assertTrue(app.game.finished)
                self.assertTrue(app.query_one("#submit-button", Button).disabled)

    async def test_rendered_board_and_keyboard_include_guessed_letters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = self.build_app(Path(temp_dir) / "history.json")

            async with app.run_test(size=(140, 40)) as pilot:
                await pilot.pause()
                app.submit_text("apple")
                await pilot.pause()

                board_capture = io.StringIO()
                keyboard_capture = io.StringIO()
                board_console = Console(file=board_capture, force_terminal=False, color_system=None, width=120)
                keyboard_console = Console(file=keyboard_capture, force_terminal=False, color_system=None, width=120)
                board_console.print(app.render_board())
                keyboard_console.print(app.render_keyboard())

                self.assertIn(" A ", board_capture.getvalue())
                self.assertIn(" P ", board_capture.getvalue())
                self.assertIn(" A ", keyboard_capture.getvalue())
                self.assertIn(" P ", keyboard_capture.getvalue())

    async def test_menu_command_opens_help_screen(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = self.build_app(Path(temp_dir) / "history.json")

            async with app.run_test(size=(140, 40)) as pilot:
                await pilot.pause()
                input_widget = app.query_one("#guess-input", Input)
                input_widget.value = "*menu"
                await pilot.click("#submit-button")
                await pilot.pause()
                self.assertEqual(len(app.screen_stack), 2)

    async def test_new_round_reenables_input_after_finish(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = self.build_app(Path(temp_dir) / "history.json")

            async with app.run_test(size=(140, 40)) as pilot:
                await pilot.pause()
                input_widget = app.query_one("#guess-input", Input)
                input_widget.value = "apple"
                await pilot.click("#submit-button")
                await pilot.pause()

                await pilot.press("n")
                await pilot.pause()

                self.assertFalse(app.game.finished)
                self.assertFalse(app.query_one("#guess-input", Input).disabled)

    async def test_win_state_matches_browser_flow_and_persists_stats(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "history.json"
            app = self.build_app(history_path)

            async with app.run_test(size=(140, 40)) as pilot:
                await pilot.pause()
                app.submit_text("apple")
                await pilot.pause()

                self.assertTrue(app.game.guess_correct)
                self.assertFalse(app.query_one("#guess-row").display)
                self.assertEqual(app.query_one("#new-round-button", Button).variant, "warning")
                self.assertTrue(history_path.exists())

                payload = json.loads(history_path.read_text())
                self.assertEqual(len(payload), 1)
                self.assertTrue(payload[0]["won"])
                self.assertEqual(payload[0]["guesses"], 1)

                await pilot.click("#banner-stats-button")
                await pilot.pause()
                self.assertEqual(len(app.screen_stack), 2)

    async def test_stats_command_opens_modal_from_toolbar_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = self.build_app(Path(temp_dir) / "history.json")

            async with app.run_test(size=(140, 40)) as pilot:
                await pilot.pause()
                app.process_command("*stats")
                await pilot.pause()
                self.assertEqual(len(app.screen_stack), 2)
