from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any, Iterable

from rich.console import Group
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Static

from src.game_engine import (
    KEYBOARD_ROWS,
    STATE_PRIORITY,
    GameSession,
    LetterState,
    Tile,
    normalize_answers,
)

HISTORY_LIMIT = 12
DEFAULT_HISTORY_PATH = Path.home() / ".wordies_recent_stats.json"
CELEBRATION_FRAMES = (
    "spark  sparkle  spark",
    "flare  ROUND SOLVED  flare",
    "confetti  you nailed it  confetti",
    "victory lap  next round?  victory lap",
)


def clone_board(board: list[list[Tile]]) -> list[list[Tile]]:
    return [[Tile(tile.letter, tile.state) for tile in row] for row in board]


def normalize_history_entry(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None

    won = bool(raw.get("won"))
    guesses = raw.get("guesses")
    timestamp = raw.get("timestamp")
    if not isinstance(guesses, int) or guesses < 1 or guesses > 6:
        return None
    if not isinstance(timestamp, int):
        return None

    label = raw.get("label")
    if not isinstance(label, str) or not label.strip():
        label = f"Win in {guesses}" if won else "Loss"

    return {
        "won": won,
        "guesses": guesses,
        "label": label,
        "timestamp": timestamp,
    }


class HelpScreen(ModalScreen[None]):
    CSS = """
    HelpScreen {
        align: center middle;
        background: rgba(15, 23, 42, 0.74);
    }

    #help-dialog {
        width: 72;
        height: auto;
        border: round #f59e0b;
        background: #111827;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(
            "\n".join(
                [
                    "Wordies Commands",
                    "",
                    "Type a five-letter guess and press Enter.",
                    "*menu  Show this help dialog",
                    "*clue  Toggle the clue hint",
                    "*debug Toggle debug details",
                    "*stats Open recent performance",
                    "*new   Start a fresh round",
                    "*quit  Exit the app",
                    "",
                    "Shortcuts",
                    "c  Toggle clue",
                    "d  Toggle debug",
                    "s  Open stats",
                    "n  Start a new round",
                    "?  Open help",
                    "q  Quit",
                    "",
                    "Press Escape to close this dialog.",
                ]
            ),
            id="help-dialog",
        )

    def on_key(self, event) -> None:  # type: ignore[override]
        if event.key in {"escape", "enter"}:
            self.dismiss()

    def on_click(self) -> None:
        self.dismiss()


class StatsScreen(ModalScreen[None]):
    CSS = """
    StatsScreen {
        align: center middle;
        background: rgba(15, 23, 42, 0.78);
    }

    #stats-shell {
        width: 82;
        height: auto;
        border: round #67e8f9 45%;
        background: #111827;
        padding: 1 2;
    }

    #stats-actions {
        height: auto;
        margin-top: 1;
    }

    #stats-actions Button {
        width: 1fr;
        margin-right: 1;
    }
    """

    def __init__(self, entries: list[dict[str, Any]]) -> None:
        super().__init__()
        self.entries = entries

    def compose(self) -> ComposeResult:
        yield Static(self.render_stats(), id="stats-shell")
        with Horizontal(id="stats-actions"):
            yield Button("New Round", id="stats-new-round-button", variant="warning")
            yield Button("Hide", id="stats-close-button")

    def render_stats(self) -> Group:
        wins = sum(1 for entry in self.entries if entry["won"])
        rounds = len(self.entries)
        win_rate = f"{round((wins / rounds) * 100)}%" if rounds else "0%"
        chart = self.build_chart()

        return Group(
            Text("RECENT PERFORMANCE", style="bold #67e8f9"),
            Text("Stored locally for your terminal sessions.", style="italic #9fb3c8"),
            Text(""),
            Text.assemble(
                ("Rounds: ", "bold #9fb3c8"),
                (str(rounds), "bold white"),
                ("   Wins: ", "bold #9fb3c8"),
                (str(wins), "bold white"),
                ("   Win Rate: ", "bold #9fb3c8"),
                (win_rate, "bold white"),
            ),
            Text(""),
            *chart,
        )

    def build_chart(self) -> list[Text]:
        if not self.entries:
            return [Text("No completed rounds yet. Finish one and the chart will light up.", style="italic #9fb3c8")]

        lines: list[Text] = []
        for index, entry in enumerate(reversed(self.entries), start=1):
            width = max(3, round((entry["guesses"] / 6) * 18))
            bar = "█" * width
            style = "#22c55e" if entry["won"] else "#f97316"
            value = f'{entry["guesses"]} guesses' if entry["won"] else "Loss"
            lines.append(
                Text.assemble(
                    (f"Round {index:>2}  ", "bold #9fb3c8"),
                    (bar.ljust(18, "·"), style),
                    ("  ", ""),
                    (value, "white"),
                )
            )
        return lines

    def on_key(self, event) -> None:  # type: ignore[override]
        if event.key == "escape":
            self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "stats-new-round-button":
            self.app.start_new_round()
            self.dismiss()
        elif event.button.id == "stats-close-button":
            self.dismiss()


class WordiesTextualApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
        background: #0f172a;
        color: #e5eef8;
    }

    #app-shell {
        height: 1fr;
        padding: 1 2;
    }

    .panel {
        border: round #7dd3fc 40%;
        background: #111827;
        padding: 1 2;
        margin-bottom: 1;
    }

    #hero {
        height: auto;
    }

    #layout {
        height: 1fr;
    }

    #main-pane {
        width: 8fr;
        margin-right: 1;
    }

    #side-pane {
        width: 7fr;
        margin-left: 1;
    }

    #board-panel,
    #play-panel,
    #keyboard-panel,
    #debug-panel,
    #celebration-panel {
        height: auto;
    }

    #status-copy {
        margin-bottom: 1;
    }

    #answer-state,
    #clue-text {
        color: #9fb3c8;
    }

    #win-banner {
        height: auto;
        margin: 1 0;
    }

    #win-banner-copy {
        width: 1fr;
        padding-right: 1;
    }

    #banner-stats-button {
        width: 18;
    }

    #guess-row,
    #toolbar-primary,
    #toolbar-secondary {
        height: auto;
        margin-top: 1;
    }

    #guess-input {
        width: 1fr;
        margin-right: 1;
    }

    #submit-button,
    #clue-button,
    #stats-button,
    #new-round-button,
    #menu-button,
    #debug-button,
    #quit-button {
        width: 1fr;
        margin-right: 1;
    }

    #debug-panel {
        display: none;
    }

    #celebration-panel {
        display: none;
    }
    """

    BINDINGS = [
        ("q", "app.quit", "Quit"),
        ("c", "toggle_clue", "Clue"),
        ("d", "toggle_debug", "Debug"),
        ("s", "show_stats", "Stats"),
        ("n", "new_round", "New Round"),
        ("question_mark", "show_help", "Help"),
    ]

    def __init__(
        self,
        word_list: Iterable[str],
        history_path: str | Path | None = None,
        animation_delay: float = 0.08,
        celebration_duration: float = 1.7,
    ) -> None:
        super().__init__()
        self.answers = normalize_answers(word_list)
        self.game = GameSession(self.answers)
        self.history_path = Path(history_path) if history_path else DEFAULT_HISTORY_PATH
        self.animation_delay = animation_delay
        self.celebration_duration = celebration_duration
        self.recent_results = self.load_recent_results()
        self.display_board = clone_board(self.game.board)
        self.display_keyboard_state = dict(self.game.keyboard_state)
        self.show_clue = False
        self.show_debug = False
        self.status_message = "Guess a five-letter word."
        self.animating_reveal = False
        self.current_round_recorded = False
        self.reveal_generation = 0
        self.celebration_generation = 0
        self.celebration_active = False
        self.celebration_frame = 0
        self.celebration_timer: Any = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="app-shell"):
            yield Static("", id="hero", classes="panel")
            with Horizontal(id="layout"):
                with Vertical(id="main-pane"):
                    yield Static("", id="board-panel", classes="panel")
                    yield Static("", id="celebration-panel", classes="panel")
                with Vertical(id="side-pane"):
                    with Vertical(id="play-panel", classes="panel"):
                        yield Static("", id="status-copy")
                        yield Static("", id="answer-state")
                        with Horizontal(id="win-banner"):
                            yield Static("", id="win-banner-copy")
                            yield Button("View Stats", id="banner-stats-button")
                        with Horizontal(id="guess-row"):
                            yield Input(placeholder="type a guess", id="guess-input")
                            yield Button("Submit", id="submit-button", variant="primary")
                        with Horizontal(id="toolbar-primary"):
                            yield Button("Show Clue", id="clue-button")
                            yield Button("Recent Stats", id="stats-button")
                            yield Button("New Round", id="new-round-button")
                        with Horizontal(id="toolbar-secondary"):
                            yield Button("Menu", id="menu-button")
                            yield Button("Toggle Debug", id="debug-button")
                            yield Button("Quit", id="quit-button", variant="error")
                        yield Static("", id="clue-text")
                    yield Static("", id="keyboard-panel", classes="panel")
                    yield Static("", id="debug-panel", classes="panel")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_view()

    def load_recent_results(self) -> list[dict[str, Any]]:
        try:
            raw = json.loads(self.history_path.read_text())
        except FileNotFoundError:
            return []
        except (json.JSONDecodeError, OSError):
            return []

        if not isinstance(raw, list):
            return []

        entries = [normalize_history_entry(entry) for entry in raw]
        return [entry for entry in entries if entry is not None][-HISTORY_LIMIT:]

    def save_recent_results(self) -> None:
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_path.write_text(json.dumps(self.recent_results[-HISTORY_LIMIT:], indent=2))

    def tile_text(self, letter: str = "", state: LetterState = LetterState.EMPTY) -> Text:
        symbol = letter.upper() if letter else " "
        style = "bold white on #1f2937"
        if state == LetterState.CORRECT:
            style = "bold black on #22c55e"
        elif state == LetterState.PRESENT:
            style = "bold black on #f59e0b"
        elif state == LetterState.ABSENT:
            style = "bold white on #64748b"
        return Text(f" {symbol} ", style=style)

    def render_hero(self) -> Group:
        return Group(
            Text("WORDIES", style="bold #67e8f9"),
            Text("Guess fast. Keep it clean.", style="bold white"),
            Text(
                "A local Textual build that mirrors the browser game with recent stats, clue toggles, and a cleaner play loop.",
                style="#9fb3c8",
            ),
        )

    def render_board_panel(self) -> Group:
        guesses_left = self.game.max_guesses - self.game.guesses_used
        rows: list[Text] = [
            Text.assemble(
                ("BOARD", "bold #9fb3c8"),
                ("   ", ""),
                (f"{guesses_left} guesses left", "bold #67e8f9"),
            ),
            Text(""),
        ]
        for row in self.display_board:
            row_text = Text()
            for index, tile in enumerate(row):
                if index:
                    row_text.append(" ")
                row_text.append_text(self.tile_text(tile.letter, tile.state))
            rows.append(row_text)
        return Group(*rows)

    def render_board(self) -> Group:
        return self.render_board_panel()

    def render_keyboard_panel(self) -> Group:
        rendered_rows: list[Text] = [Text("KEYBOARD", style="bold #9fb3c8"), Text("")]
        for row in KEYBOARD_ROWS:
            row_text = Text()
            for letter in row:
                if letter == " ":
                    row_text.append("   ")
                    continue
                state = self.display_keyboard_state[letter.lower()]
                if row_text.plain.strip():
                    row_text.append(" ")
                row_text.append_text(self.tile_text(letter, state))
            rendered_rows.append(row_text)
        return Group(*rendered_rows)

    def render_keyboard(self) -> Group:
        return self.render_keyboard_panel()

    def render_win_banner(self) -> Group:
        return Group(
            Text("ROUND SOLVED", style="bold #22c55e"),
            Text("Take the win lap, check your recent run, then jump into the next round.", style="#9fb3c8"),
        )

    def render_debug(self) -> Group:
        return Group(
            Text("DEBUG", style="bold #f472b6"),
            Text(f"Answer: {self.game.answer.upper()}"),
            Text(f"Answers available: {len(self.answers)}"),
            Text(f"Recorded rounds: {len(self.recent_results)}"),
        )

    def render_celebration(self) -> Group:
        frame = CELEBRATION_FRAMES[self.celebration_frame % len(CELEBRATION_FRAMES)]
        return Group(
            Text("WIN CELEBRATION", style="bold #f59e0b"),
            Text(frame.upper(), style="bold #67e8f9"),
        )

    def render_clue_text(self) -> Text:
        if not self.show_clue:
            return Text("")
        return Text(f"Clue: {self.game.clue()}", style="bold #f59e0b")

    def render_answer_state(self) -> Text:
        if self.game.guess_correct:
            return Text("Solved locally on your machine. Start the next round when you are ready.", style="#9fb3c8")
        if self.game.finished:
            return Text(f"The answer was {self.game.answer.upper()}. Start a new round to keep playing.", style="#9fb3c8")
        return Text("Local mode is running on your machine.", style="#9fb3c8")

    def set_letter_state(self, letter: str, state: LetterState) -> None:
        current = self.display_keyboard_state[letter]
        if STATE_PRIORITY[state] > STATE_PRIORITY[current]:
            self.display_keyboard_state[letter] = state

    def set_controls_state(self) -> None:
        finished = self.game.finished
        win = self.game.guess_correct
        controls_disabled = finished or self.animating_reveal

        guess_input = self.query_one("#guess-input", Input)
        submit_button = self.query_one("#submit-button", Button)
        guess_row = self.query_one("#guess-row", Horizontal)
        guess_row.display = not win
        guess_input.disabled = controls_disabled
        submit_button.disabled = controls_disabled

        clue_button = self.query_one("#clue-button", Button)
        clue_button.label = "Hide Clue" if self.show_clue else "Show Clue"

        debug_button = self.query_one("#debug-button", Button)
        debug_button.label = "Hide Debug" if self.show_debug else "Show Debug"

        new_round_button = self.query_one("#new-round-button", Button)
        new_round_button.variant = "warning" if win else "default"

        win_banner = self.query_one("#win-banner", Horizontal)
        win_banner.display = win
        self.query_one("#banner-stats-button", Button).variant = "primary" if win else "default"

        debug_panel = self.query_one("#debug-panel", Static)
        debug_panel.display = self.show_debug

        celebration_panel = self.query_one("#celebration-panel", Static)
        celebration_panel.display = self.celebration_active

    def refresh_view(self) -> None:
        self.query_one("#hero", Static).update(self.render_hero())
        self.query_one("#board-panel", Static).update(self.render_board_panel())
        self.query_one("#status-copy", Static).update(Text(self.status_message, style="bold white"))
        self.query_one("#answer-state", Static).update(self.render_answer_state())
        self.query_one("#win-banner-copy", Static).update(self.render_win_banner())
        self.query_one("#clue-text", Static).update(self.render_clue_text())
        self.query_one("#keyboard-panel", Static).update(self.render_keyboard_panel())
        self.query_one("#debug-panel", Static).update(self.render_debug())
        self.query_one("#celebration-panel", Static).update(self.render_celebration())
        self.set_controls_state()

    def action_toggle_clue(self) -> None:
        self.toggle_clue()

    def action_toggle_debug(self) -> None:
        self.toggle_debug()

    def action_new_round(self) -> None:
        self.start_new_round()

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_show_stats(self) -> None:
        self.push_screen(StatsScreen(self.recent_results))

    def start_new_round(self) -> None:
        self.reveal_generation += 1
        self.stop_celebration()
        self.game.reset_round()
        self.display_board = clone_board(self.game.board)
        self.display_keyboard_state = dict(self.game.keyboard_state)
        self.current_round_recorded = False
        self.status_message = "Guess a five-letter word."
        self.refresh_view()
        guess_input = self.query_one("#guess-input", Input)
        guess_input.value = ""
        guess_input.focus()

    def toggle_clue(self) -> None:
        self.show_clue = not self.show_clue
        self.status_message = f"Clue {'shown' if self.show_clue else 'hidden'}."
        self.refresh_view()

    def toggle_debug(self) -> None:
        self.show_debug = not self.show_debug
        self.status_message = f"Debug {'shown' if self.show_debug else 'hidden'}."
        self.refresh_view()

    def stop_celebration(self) -> None:
        self.celebration_generation += 1
        self.celebration_active = False
        self.celebration_frame = 0
        if self.celebration_timer is not None:
            self.celebration_timer.stop()
            self.celebration_timer = None

    def start_celebration(self) -> None:
        self.stop_celebration()
        if self.celebration_duration <= 0:
            return

        generation = self.celebration_generation
        self.celebration_active = True
        self.celebration_frame = 0

        def advance_frame() -> None:
            if generation != self.celebration_generation:
                return
            self.celebration_frame = (self.celebration_frame + 1) % len(CELEBRATION_FRAMES)
            self.refresh_view()

        def finish() -> None:
            if generation != self.celebration_generation:
                return
            self.stop_celebration()
            self.refresh_view()

        interval = max(0.12, self.celebration_duration / len(CELEBRATION_FRAMES))
        self.celebration_timer = self.set_interval(interval, advance_frame)
        self.set_timer(self.celebration_duration, finish)

    def record_completed_round(self) -> None:
        if self.current_round_recorded:
            return

        guesses = self.game.guesses_used if self.game.guess_correct else self.game.max_guesses
        entry = {
            "won": self.game.guess_correct,
            "guesses": guesses,
            "label": f"Win in {guesses}" if self.game.guess_correct else "Loss",
            "timestamp": int(time()),
        }
        self.recent_results.append(entry)
        self.recent_results = self.recent_results[-HISTORY_LIMIT:]
        self.save_recent_results()
        self.current_round_recorded = True

    def complete_round(self) -> None:
        self.record_completed_round()
        if self.game.guess_correct:
            self.status_message = f"You won in {self.game.guesses_used} guesses."
            self.start_celebration()
        else:
            self.status_message = f"Out of guesses. The answer was {self.game.answer.upper()}."
        self.refresh_view()

    def process_command(self, command: str) -> None:
        if command == "*menu":
            self.status_message = "Opening the help menu."
            self.refresh_view()
            self.push_screen(HelpScreen())
        elif command == "*clue":
            self.toggle_clue()
        elif command == "*debug":
            self.toggle_debug()
        elif command == "*stats":
            self.status_message = "Opening recent stats."
            self.refresh_view()
            self.push_screen(StatsScreen(self.recent_results))
        elif command in {"*new", "*reset"}:
            self.start_new_round()
        elif command == "*quit":
            self.exit()
        else:
            self.status_message = "Unknown command. Type *menu to see the options."
            self.refresh_view()

    def reveal_tile(self, generation: int, row_index: int, tile_index: int) -> None:
        if generation != self.reveal_generation:
            return

        tile = self.game.board[row_index][tile_index]
        self.display_board[row_index][tile_index] = tile
        self.set_letter_state(tile.letter, tile.state)
        self.refresh_view()

    def finish_reveal(self, generation: int) -> None:
        if generation != self.reveal_generation:
            return

        self.animating_reveal = False
        if self.game.finished:
            self.complete_round()
        else:
            self.status_message = "Keep going."
            self.refresh_view()
            self.query_one("#guess-input", Input).focus()

    def animate_latest_guess(self, row_index: int) -> None:
        self.animating_reveal = True
        self.reveal_generation += 1
        generation = self.reveal_generation
        self.status_message = "Checking guess..."
        self.display_board[row_index] = [Tile() for _ in range(self.game.answer_len)]
        self.refresh_view()

        if self.animation_delay <= 0:
            for tile_index in range(self.game.answer_len):
                self.reveal_tile(generation, row_index, tile_index)
            self.finish_reveal(generation)
            return

        for tile_index in range(self.game.answer_len):
            self.set_timer(
                self.animation_delay * (tile_index + 1),
                lambda idx=tile_index: self.reveal_tile(generation, row_index, idx),
            )
        self.set_timer(
            self.animation_delay * (self.game.answer_len + 1),
            lambda: self.finish_reveal(generation),
        )

    def submit_text(self, value: str) -> None:
        if self.animating_reveal:
            self.status_message = "Reveal in progress. Give it a beat."
            self.refresh_view()
            return

        guess = value.strip().lower()
        guess_input = self.query_one("#guess-input", Input)
        guess_input.value = ""

        if not guess:
            self.status_message = "Enter a five-letter word to keep playing."
            self.refresh_view()
            return

        if guess.startswith("*"):
            self.process_command(guess)
            return

        validation_error = self.game.validate_guess(guess)
        if validation_error:
            self.status_message = validation_error
            self.refresh_view()
            return

        error, accepted = self.game.submit_guess(guess)
        if error or not accepted:
            self.status_message = error or "Guess was not accepted."
            self.refresh_view()
            return

        self.animate_latest_guess(self.game.guesses_used - 1)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "guess-input":
            self.submit_text(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "submit-button":
            self.submit_text(self.query_one("#guess-input", Input).value)
        elif button_id == "menu-button":
            self.process_command("*menu")
        elif button_id == "clue-button":
            self.toggle_clue()
        elif button_id == "debug-button":
            self.toggle_debug()
        elif button_id in {"stats-button", "banner-stats-button"}:
            self.action_show_stats()
        elif button_id == "new-round-button":
            self.start_new_round()
        elif button_id == "quit-button":
            self.exit()
