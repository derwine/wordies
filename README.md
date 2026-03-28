<h1>Wordies</h1>

```text
__      _____  _ __ __| |_  ___  ___
\ \ /\ / / _ \| '__/ _` | |/ _ \/ __|
 \ V  V / (_) | | | (_| | |  __/\__ \
  \_/\_/ \___/|_|  \__,_|_|\___||___/
```

An unlimited five-letter word guessing game for the terminal, inspired by <a href="https://www.nytimes.com/games/wordle/index.html" target="_blank">Wordle</a>.

## Highlights

- Modern terminal UI powered by <a href="https://github.com/Textualize/rich" target="_blank">Rich</a>
- Wordle-style duplicate letter scoring
- Optional clue and debug modes
- Session histogram that tracks how many guesses your wins took
- Curated five-letter answers built from the included word list

## Installation

You will need <a href="https://python-poetry.org/" target="_blank">Poetry</a>.

```bash
pip install poetry
poetry install
```

Start the game with:

```bash
poetry run start-game
```

Launch the local browser version with:

```bash
poetry run start-game --browser
```

## How To Play

- You get 6 chances to guess a 5-letter word.
- Green means the letter is in the correct spot.
- Amber means the letter exists in the answer but is in the wrong spot.
- Gray means the letter is not in the answer.
- Use `Ctrl+C` to quit at any time.

## Commands

Type one of these commands at the guess prompt:

- `*menu` shows the available commands
- `*clue` toggles a first-letter and last-letter clue
- `*debug` toggles debug information for development
- `*quit` exits the game

## Browser Mode

- `poetry run start-game --browser` starts a local web server and opens Wordies in your browser
- Use `--host` and `--port` if you want to bind to a different local address, for example `poetry run start-game --browser --port 9000`
- Browser mode keeps the same word rules and scoring as the terminal version
- Winning rounds trigger a celebration animation and spotlight the existing `New Round` action
- `Recent Stats` opens a local-storage-backed popup with your recent wins, losses, and guess counts

## Regression Checks

- Run the current regression suite with `./scripts/run_regression_checks.sh`
- The repo now includes a `.githooks/post-commit` hook that runs the same checks after every commit
- If you clone the repo elsewhere, re-enable the repo-local hooks with `git config core.hooksPath .githooks`

## Customization

The project is intentionally small, so it is easy to tweak:

- Update the answer source in [src/clues.py](src/clues.py) to change the vocabulary
- Adjust colors, panels, and board styles in [src/wordies.py](src/wordies.py)
- Swap the dictionary source in `VALID_WORDS` if you want looser or stricter validation
- Change `max_guesses` or `answer_len` if you want to experiment with other game modes

## Future UI Directions

If you want the project to feel even more modern, these are the best next steps:

- Stay in the terminal and move to <a href="https://textual.textualize.io/" target="_blank">Textual</a> for layouts, key bindings, and richer interactions
- Build a lightweight browser version with <a href="https://nicegui.io/" target="_blank">NiceGUI</a> if you want a Python-first web UI
- Explore <a href="https://reflex.dev/" target="_blank">Reflex</a> if you want a more app-like Python web stack with component-driven pages

## Word List Credit

The answer list is adapted from https://www.ef.edu/english-resources/english-vocabulary/top-3000-words/
