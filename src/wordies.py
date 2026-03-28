from __future__ import annotations

from collections import Counter
from typing import Iterable

from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from src.game_engine import (
    KEYBOARD_ROWS,
    GameSession,
    LetterState,
    evaluate_guess,
    normalize_answers,
)


class Wordies:
    EMPTY_TILE_STYLE = "bold white on rgb(31,41,55)"
    ABSENT_TILE_STYLE = "bold white on rgb(107,114,128)"
    PRESENT_TILE_STYLE = "bold white on rgb(180,126,17)"
    CORRECT_TILE_STYLE = "bold white on rgb(22,163,74)"
    PANEL_BORDER_STYLE = "bright_cyan"
    STATUS_STYLES = {
        "info": "bold cyan",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
    }
    def __init__(self, word_list: Iterable[str], console: Console | None = None) -> None:
        self.console = console or Console()
        self.answers = normalize_answers(word_list)
        self.show_debug = False
        self.show_clue = False
        self.completed_games_guesses: list[int] = []
        self.status_message = "Guess a five-letter word."
        self.status_kind = "info"
        self.game = GameSession(self.answers)

    def start_new_round(self) -> None:
        self.game.reset_round()
        self.set_status("Guess a five-letter word.", "info")

    def set_status(self, message: str, kind: str = "info") -> None:
        self.status_message = message
        self.status_kind = kind

    def tile_style(self, state: LetterState) -> str:
        return {
            LetterState.EMPTY: self.EMPTY_TILE_STYLE,
            LetterState.ABSENT: self.ABSENT_TILE_STYLE,
            LetterState.PRESENT: self.PRESENT_TILE_STYLE,
            LetterState.CORRECT: self.CORRECT_TILE_STYLE,
        }[state]

    def render_tile(self, letter: str = "", state: LetterState = LetterState.EMPTY) -> Text:
        display = f"[ {letter.upper() if letter else ' '} ]"
        return Text(display, style=self.tile_style(state), justify="center")

    def build_header_panel(self) -> Panel:
        help_text = Text()
        help_text.append("Guess the hidden five-letter word in six tries.\n", style="bold white")
        help_text.append("Commands: ", style="bold cyan")
        help_text.append("*menu", style="bold white")
        help_text.append(", ")
        help_text.append("*clue", style="bold white")
        help_text.append(", ")
        help_text.append("*debug", style="bold white")
        help_text.append(", ")
        help_text.append("*quit", style="bold white")
        help_text.append("\n")
        help_text.append("Legend: ", style="bold cyan")
        help_text.append("green = correct", style=self.CORRECT_TILE_STYLE)
        help_text.append("  ")
        help_text.append("amber = present", style=self.PRESENT_TILE_STYLE)
        help_text.append("  ")
        help_text.append("gray = absent", style=self.ABSENT_TILE_STYLE)
        return Panel(
            help_text,
            title="WORDIES",
            border_style=self.PANEL_BORDER_STYLE,
            padding=(1, 2),
        )

    def build_board(self) -> Panel:
        board = Table.grid(padding=(0, 1))
        for _ in range(self.game.answer_len):
            board.add_column(justify="center")
        for row in self.game.board:
            board.add_row(*(self.render_tile(tile.letter, tile.state) for tile in row))
        return Panel(board, title="Board", border_style=self.PANEL_BORDER_STYLE)

    def build_keyboard(self) -> Panel:
        keyboard = Table.grid(padding=(0, 0))
        keyboard.add_column()
        for row in KEYBOARD_ROWS:
            line = Text()
            for letter in row:
                if letter == " ":
                    line.append("  ")
                    continue
                state = self.game.keyboard_state[letter.lower()]
                line.append_text(self.render_tile(letter, state))
                line.append(" ")
            keyboard.add_row(line)
        return Panel(keyboard, title="Keyboard", border_style=self.PANEL_BORDER_STYLE)

    def build_status_panel(self) -> Panel:
        style = self.STATUS_STYLES.get(self.status_kind, self.STATUS_STYLES["info"])
        status = Text(self.status_message, style=style)
        status.append(
            f"\nGuesses left: {self.game.max_guesses - self.game.guesses_used}",
            style="white",
        )
        return Panel(status, title="Status", border_style=self.PANEL_BORDER_STYLE)

    def build_clue_panel(self) -> Panel | None:
        if not self.show_clue:
            return None
        clue = self.game.clue()
        return Panel(
            Text(clue, style="bold yellow"),
            title="Clue",
            border_style="yellow",
        )

    def build_debug_panel(self) -> Panel | None:
        if not self.show_debug:
            return None
        debug_text = Text()
        debug_text.append(f"Answer: {self.game.answer.upper()}\n", style="bold magenta")
        debug_text.append(f"Answers available: {len(self.answers)}\n", style="white")
        debug_text.append("Validation source: english_words web2 + answers", style="white")
        return Panel(debug_text, title="Debug", border_style="magenta")

    def build_histogram_panel(self) -> Panel:
        histogram = Table.grid(expand=True)
        histogram.add_column(justify="right", width=2)
        histogram.add_column()
        histogram.add_column(justify="right", width=2)

        counts = Counter(self.completed_games_guesses)
        for guess_number in range(1, self.game.max_guesses + 1):
            count = counts[guess_number]
            bar = "■" * count if count else "·"
            histogram.add_row(
                Text(str(guess_number), style="bold cyan"),
                Text(bar, style="bold green" if count else "dim"),
                Text(str(count), style="white"),
            )

        title = "Win Histogram"
        if not self.completed_games_guesses:
            title = "Win Histogram (first win pending)"
        return Panel(histogram, title=title, border_style=self.PANEL_BORDER_STYLE)

    def render(self) -> None:
        self.console.clear()
        panels = [
            self.build_header_panel(),
            self.build_board(),
            self.build_keyboard(),
            self.build_status_panel(),
            self.build_histogram_panel(),
        ]
        clue_panel = self.build_clue_panel()
        if clue_panel:
            panels.append(clue_panel)
        debug_panel = self.build_debug_panel()
        if debug_panel:
            panels.append(debug_panel)
        self.console.print(Group(*panels))

    def record_guess(self, guess: str) -> None:
        error, accepted = self.game.submit_guess(guess)
        if error or not accepted:
            raise ValueError(error or "Guess was not accepted.")

    def process_menu(self, command: str) -> None:
        if command == "*menu":
            self.set_status("Commands: *menu, *clue, *debug, *quit", "info")
        elif command == "*clue":
            self.show_clue = not self.show_clue
            state = "enabled" if self.show_clue else "disabled"
            self.set_status(f"Clue mode {state}.", "warning")
        elif command == "*debug":
            self.show_debug = not self.show_debug
            state = "enabled" if self.show_debug else "disabled"
            self.set_status(f"Debug mode {state}.", "warning")
        elif command == "*quit":
            self.console.print("[bold cyan]Thanks for playing Wordies.[/]")
            raise SystemExit(0)
        else:
            self.set_status("Unknown command. Type *menu to see the options.", "error")

    def validate_guess(self, guess: str) -> str | None:
        return self.game.validate_guess(guess)

    def prompt_for_guess(self) -> str:
        return Prompt.ask("[bold cyan]Guess a word[/]").strip().lower()

    def finish_round(self) -> bool:
        if self.game.guess_correct:
            self.completed_games_guesses.append(self.game.guesses_used)
            self.set_status(f"You won in {self.game.guesses_used} guesses.", "success")
        else:
            self.set_status(
                f"Out of guesses. The answer was {self.game.answer.upper()}.",
                "error",
            )

        self.render()
        play_again = Confirm.ask("[bold cyan]Play again?[/]", default=True)
        if play_again:
            self.start_new_round()
            return True

        self.console.print("[bold cyan]Thanks for playing Wordies.[/]")
        return False

    def start(self) -> None:
        while True:
            self.start_new_round()
            while not self.game.guess_correct and self.game.guesses_used < self.game.max_guesses:
                self.render()
                guess = self.prompt_for_guess()

                if not guess:
                    self.set_status("Enter a five-letter word to keep playing.", "error")
                    continue

                if guess.startswith("*"):
                    self.process_menu(guess)
                    continue

                validation_error = self.validate_guess(guess)
                if validation_error:
                    self.set_status(validation_error, "error")
                    continue

                self.record_guess(guess)
                if self.game.guess_correct:
                    self.set_status("Solved.", "success")
                else:
                    self.set_status("Keep going.", "info")

            if not self.finish_round():
                break


def main() -> None:
    raise SystemExit("Run the game via main.py or the Poetry entry point.")


if __name__ == "__main__":
    main()
