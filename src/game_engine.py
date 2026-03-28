from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from english_words import get_english_words_set

VALID_WORDS = get_english_words_set(["web2"], lower=True)
KEYBOARD_ROWS = ("QWERTYUIOP", " ASDFGHJKL", "   ZXCVBNM")


class LetterState(str, Enum):
    EMPTY = "empty"
    ABSENT = "absent"
    PRESENT = "present"
    CORRECT = "correct"


@dataclass(frozen=True)
class Tile:
    letter: str = ""
    state: LetterState = LetterState.EMPTY


STATE_PRIORITY = {
    LetterState.EMPTY: 0,
    LetterState.ABSENT: 1,
    LetterState.PRESENT: 2,
    LetterState.CORRECT: 3,
}


def normalize_answers(word_list: Iterable[str]) -> tuple[str, ...]:
    answers = []
    seen = set()
    for word in word_list:
        cleaned = word.strip().lower()
        if len(cleaned) == 5 and cleaned.isalpha() and cleaned not in seen:
            answers.append(cleaned)
            seen.add(cleaned)

    if not answers:
        raise ValueError("Wordies requires at least one valid five-letter answer.")

    return tuple(answers)


def empty_board(answer_len: int, max_guesses: int) -> list[list[Tile]]:
    return [[Tile() for _ in range(answer_len)] for _ in range(max_guesses)]


def empty_keyboard_state() -> dict[str, LetterState]:
    return {
        letter.lower(): LetterState.EMPTY
        for row in KEYBOARD_ROWS
        for letter in row
        if letter != " "
    }


def update_keyboard_state(
    keyboard_state: dict[str, LetterState],
    guess: str,
    states: list[LetterState],
) -> None:
    for letter, state in zip(guess, states):
        current = keyboard_state[letter]
        if STATE_PRIORITY[state] > STATE_PRIORITY[current]:
            keyboard_state[letter] = state


def evaluate_guess(guess: str, answer: str) -> list[LetterState]:
    states = [LetterState.ABSENT] * len(guess)
    remaining_letters = Counter()

    for index, (guess_letter, answer_letter) in enumerate(zip(guess, answer)):
        if guess_letter == answer_letter:
            states[index] = LetterState.CORRECT
        else:
            remaining_letters[answer_letter] += 1

    for index, guess_letter in enumerate(guess):
        if states[index] == LetterState.CORRECT:
            continue
        if remaining_letters[guess_letter] > 0:
            states[index] = LetterState.PRESENT
            remaining_letters[guess_letter] -= 1

    return states


@dataclass
class GameSession:
    answers: tuple[str, ...] | list[str]
    max_guesses: int = 6
    answer_len: int = 5
    answer: str = field(init=False)
    guesses_used: int = field(init=False, default=0)
    board: list[list[Tile]] = field(init=False)
    keyboard_state: dict[str, LetterState] = field(init=False)
    guess_correct: bool = field(init=False, default=False)
    finished: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self.answers = normalize_answers(self.answers)
        self.reset_round()

    def reset_round(self) -> None:
        self.guesses_used = 0
        self.answer = random.choice(self.answers)
        self.board = empty_board(self.answer_len, self.max_guesses)
        self.keyboard_state = empty_keyboard_state()
        self.guess_correct = False
        self.finished = False

    def validate_guess(self, guess: str) -> str | None:
        if len(guess) != self.answer_len:
            return f"Word must be {self.answer_len} letters long."
        if not guess.isalpha():
            return "Word must only contain letters A-Z."
        if guess not in VALID_WORDS and guess not in self.answers:
            return "That guess is not in the word list."
        return None

    def submit_guess(self, guess: str) -> tuple[str | None, bool]:
        if self.finished:
            return "This round is finished. Start a new round to keep playing.", False

        error = self.validate_guess(guess)
        if error:
            return error, False

        states = evaluate_guess(guess, self.answer)
        self.board[self.guesses_used] = [
            Tile(letter=letter, state=state) for letter, state in zip(guess, states)
        ]
        update_keyboard_state(self.keyboard_state, guess, states)
        self.guesses_used += 1
        self.guess_correct = guess == self.answer
        self.finished = self.guess_correct or self.guesses_used >= self.max_guesses
        return None, True

    def clue(self) -> str:
        return f"{self.answer[0].upper()}***{self.answer[-1].upper()}"

    def board_rows(self) -> list[list[dict[str, str]]]:
        return [
            [{"letter": tile.letter, "state": tile.state.value} for tile in row]
            for row in self.board
        ]

    def keyboard_rows(self) -> list[list[dict[str, str]]]:
        rows = []
        for row in KEYBOARD_ROWS:
            rows.append(
                [
                    {
                        "letter": letter,
                        "state": self.keyboard_state[letter.lower()].value,
                    }
                    for letter in row
                    if letter != " "
                ]
            )
        return rows

    def status(self) -> str:
        if self.guess_correct:
            return f"You won in {self.guesses_used} guesses."
        if self.finished:
            return f"Out of guesses. The answer was {self.answer.upper()}."
        return "Guess a five-letter word."

