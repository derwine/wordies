import unittest

from src.clues import answers
from src.game_engine import GameSession, LetterState, evaluate_guess, empty_keyboard_state, update_keyboard_state
from src.wordies import Wordies


class WordiesTests(unittest.TestCase):
    def test_answers_are_normalized(self) -> None:
        game = Wordies(answers)
        self.assertTrue(game.answers)
        self.assertEqual(len(game.answers), len(set(game.answers)))
        self.assertTrue(all(word.isalpha() and word.islower() and len(word) == 5 for word in game.answers))

    def test_duplicate_letters_are_scored_like_wordle(self) -> None:
        states = evaluate_guess("allee", "apple")
        self.assertEqual(
            states,
            [
                LetterState.CORRECT,
                LetterState.PRESENT,
                LetterState.ABSENT,
                LetterState.ABSENT,
                LetterState.CORRECT,
            ],
        )

    def test_keyboard_state_keeps_best_result(self) -> None:
        keyboard_state = empty_keyboard_state()
        update_keyboard_state(
            keyboard_state,
            "allee",
            [
                LetterState.ABSENT,
                LetterState.PRESENT,
                LetterState.ABSENT,
                LetterState.ABSENT,
                LetterState.CORRECT,
            ],
        )
        update_keyboard_state(
            keyboard_state,
            "angle",
            [
                LetterState.CORRECT,
                LetterState.ABSENT,
                LetterState.ABSENT,
                LetterState.PRESENT,
                LetterState.CORRECT,
            ],
        )
        self.assertEqual(keyboard_state["a"], LetterState.CORRECT)
        self.assertEqual(keyboard_state["l"], LetterState.PRESENT)
        self.assertEqual(keyboard_state["e"], LetterState.CORRECT)

    def test_invalid_characters_are_rejected_before_dictionary_check(self) -> None:
        game = Wordies(["apple"])
        self.assertEqual(game.validate_guess("ab1de"), "Word must only contain letters A-Z.")

    def test_game_session_finishes_on_win(self) -> None:
        session = GameSession(["apple"])
        error, accepted = session.submit_guess("apple")
        self.assertIsNone(error)
        self.assertTrue(accepted)
        self.assertTrue(session.guess_correct)
        self.assertTrue(session.finished)


if __name__ == "__main__":
    unittest.main()
